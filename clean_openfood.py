"""
Open Food Facts – Data Cleaning Pipeline

This script loads raw product data from the Open Food Facts dataset and applies
a structured, modular cleaning process to prepare the data for analysis.

Main cleaning steps:
- HTML unescaping and string normalization
- Handling missing values and known junk entries
- Cleaning category, country, and label fields
- Capping outliers in nutritional columns
- Mapping qualitative scores (e.g., NutriScore, NOVA group) to readable formats

Output: A cleaned CSV file ready for EDA, dashboarding, or modeling.
"""

import pandas as pd
import numpy as np
import re
import html
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Define file path
data_path = Path(r"C:\Users\babul\OneDrive\Desktop\deluluu\sara\working_openfood.csv") 

# Load data
def load_data(path: Path) -> pd.DataFrame:
    print("\n" + "="*35)
    print("🧼 DATA CLEANING REPORT — Open Food Facts")
    print("="*35)
    logger.info("📂 Loading data...")
    df = pd.read_csv(path)
    logger.info(f"✅ Data loaded with shape: {df.shape}")
    return df

# Utility function

def remove_lang_prefix(text):
    if isinstance(text, str):
        return re.sub(r'^[a-z]{2}[:_]', '', text, flags=re.IGNORECASE).strip()
    return text

# Cleaning Functions

def clean_product_name(df):
    logger.info("🧹 Cleaning product_name column")
    df["product_name"] = df["product_name"].apply(lambda x: html.unescape(x) if pd.notnull(x) else x)
    df["product_name"] = df["product_name"].str.strip().str.title()
    df = df[df["product_name"] != "Xxx"].copy()  # ✅ Prevents SettingWithCopyWarning
    df["product_name"] = df["product_name"].fillna("Unknown")
    return df

def clean_brands(df):
    logger.info("🧹 Cleaning brands column")
    df["brands"] = df["brands"].apply(lambda x: html.unescape(x) if pd.notnull(x) else x)
    df["brands"] = df["brands"].str.title().str.strip()
    df["brands"] = df["brands"].replace("Xylimgxyling", "Unknown")
    df["brands"] = df["brands"].str.replace("’", "'", regex=False)
    df["brands"] = df["brands"].str.replace(", ", ",", regex=False).str.replace(",", ", ", regex=False)
    df["brands"] = df["brands"].fillna("Unknown")
    return df

def clean_categories(df):
    logger.info("🧹 Cleaning categories column")
    df["categories"] = df["categories"].replace(["undefined", "za"], pd.NA)
    df["categories"] = df["categories"].str.strip().fillna("Unknown").apply(remove_lang_prefix)
    df["categories_top"] = df["categories"].str.split(",").str[0].str.title().fillna("Unknown")
    return df

def clean_countries(df):
    logger.info("🧹 Cleaning countries column")
    df["countries"] = df["countries"].str.replace(r"\b\w{2,3}:", "", regex=True)
    df["countries"] = df["countries"].str.strip().str.replace(", ", ",", regex=False).str.replace(",", ", ", regex=False).str.title()
    df["countries"] = df["countries"].fillna("Unknown")
    country_map = {
        "Fr": "France", "De": "Germany", "Gb": "United Kingdom", "Us": "United States", "Uk": "United Kingdom",
        "España": "Spain", "Espana": "Spain", "Francia": "France", "Frankreich": "France",
        "Vereinigte Staaten Von Amerika": "United States", "Brasil": "Brazil", "Brasilien": "Brazil",
        "Griechenland": "Greece", "Irland": "Ireland", "Alemania": "Germany", "Belgien": "Belgium",
        "Selestosina": "Unknown", "Ca": "Canada", "European Union": "European Union", "World": "World"
    }
    df["countries"] = df["countries"].apply(lambda x: ", ".join(country_map.get(c.strip(), c.strip()) for c in x.split(",")))
    return df

def clean_ingredients_labels_packaging(df):
    logger.info("🧹 Cleaning ingredients_text, labels, packaging")
    df["ingredients_text"] = df["ingredients_text"].fillna("Unknown").str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    df["labels"] = df["labels"].fillna("Unknown").str.replace(r"\b\w{2,3}:", "", regex=True).str.lower().str.replace(", ", ",", regex=False).str.replace(",", ", ", regex=False)
    df["packaging"] = df["packaging"].str.replace(r"\b\w{2,3}:", "", regex=True).str.replace(", ", ",", regex=False).str.replace(",", ", ", regex=False).str.strip().fillna("Unknown").str.title()
    df["packaging"] = df["packaging"].replace(["40g", "packaging", "plaza vea", "za"], "Unknown")
    return df

def clean_nutriscore(df):
    logger.info("🧹 Cleaning nutriscore_grade")
    df["nutriscore_grade"] = df["nutriscore_grade"].fillna("unknown").replace("not-applicable", "Unknown").str.lower()
    nutri_map = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "unknown": 0}
    df["nutriscore_numeric"] = df["nutriscore_grade"].map(nutri_map)
    df.drop(columns=["environmental_score_score"], inplace=True)
    return df

def clean_nova_group(df):
    logger.info("🧹 Cleaning nova_group")
    df["nova_group"] = df["nova_group"].fillna("unknown")
    nova_map = {
        1: "Unprocessed or Minimally Processed",
        2: "Processed Culinary Ingredients",
        3: "Processed Foods",
        4: "Ultra-Processed Foods", "unknown": "Unknown"
    }
    df["nova_group_label"] = df["nova_group"].map(nova_map)

    return df

def clean_nutritional_columns(df):
    logger.info("🧹 Cleaning nutritional numeric columns")
    num_cols = [
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g", "sugars_100g",
        "salt_100g", "proteins_100g", "fiber_100g", "carbohydrates_100g"
    ]
    for col in num_cols:
        df.loc[(df[col] < 0) | (df[col] > 1000), col] = np.nan
        df[col] = df[col].fillna(df[col].median()).astype("float32")
    return df

# Save cleaned file
def save_data(df, filename="cleaned_openfood.csv"):
    df.to_csv(filename, index=False)
    logger.info(f"✅ Cleaned data saved to {filename}")


def show_cleaning_summary(df: pd.DataFrame, original_shape: tuple) -> pd.DataFrame:
    logger.info("📊 Generating cleaning summary...")

    cleaned_shape = df.shape
    removed_rows = original_shape[0] - cleaned_shape[0]
    removed_cols = original_shape[1] - cleaned_shape[1]

    print("\n" + "="*35)
    print("✅ CLEANING SUMMARY")
    print("="*35)
    print(f"📐 Original Shape      : {original_shape}")
    print(f"📐 Cleaned Shape       : {cleaned_shape}")
    print(f"➖ Rows Removed         : {removed_rows}")
    print(f"➖ Columns Removed      : {removed_cols}")

    print("\n🔍 TRANSFORMATIONS SUMMARY")
    print("- product_name: HTML unescaped, stripped, title-cased, filled missing with 'Unknown', and removed 'Xxx'")
    print("- brands: Cleaned casing, spacing, and punctuation; replaced known bad values; filled NAs")
    print("- categories: Cleaned hierarchy; extracted top-level; handled undefined/unknown")
    print("- countries: Normalized codes to country names; unified formatting and naming")
    print("- ingredients_text / labels / packaging: Cleaned formatting, lang codes removed, lower/title cased")
    print("- nutriscore_grade: Normalized to lowercase, 'not-applicable' fixed; mapped to numeric score")
    print("- nova_group: Nulls filled with 'unknown'; mapped to readable labels")
    print("- nutritional columns: Outliers capped, filled missing with median, converted to float32")
    print("- Dropped: 'environmental_score_score' column (too sparse or irrelevant)")

    print("\n🧪 MISSING VALUE CHECK")
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if not missing.empty:
        print("🚨 Remaining missing values (top 10):")
        print(missing.head(10))
    else:
        print("🎉 No missing values left!")

    print("="*35 + "\n")
    return df


import time 
# Run Cleaning Pipeline
def run_pipeline():
    start = time.time()
    df = load_data(data_path)
    duplicate_rows = df.duplicated().sum()
    logger.info(f"🔁 Duplicate rows found: {duplicate_rows}")
    df = df.drop_duplicates() 
    original_shape = df.shape
    df = clean_product_name(df)
    df = clean_brands(df)
    df = clean_categories(df)
    df = clean_countries(df)
    df = clean_ingredients_labels_packaging(df)
    df = clean_nutriscore(df)
    df = clean_nova_group(df)
    df = clean_nutritional_columns(df)
    logger.info("🎉 All cleaning steps completed.")
    save_data(df)
    end = time.time()
    logger.info(f"⏱️ Pipeline finished in {end - start:.2f} seconds")
    df = show_cleaning_summary(df, original_shape)


if __name__ == "__main__":
    run_pipeline()


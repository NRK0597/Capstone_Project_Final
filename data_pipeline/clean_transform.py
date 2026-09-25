"""
Module 1-Step 2: Reads data/raw_books.csv and produces data/clean_books.csv.
"""
import os
import re
import pandas as pd

GBP_TO_INR_RATE = 105.50

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_PATH = os.path.join(DATA_DIR, "raw_books.csv")
CLEAN_PATH = os.path.join(DATA_DIR, "clean_books.csv")


def parse_price(value: str):
    if pd.isna(value):
        return float("nan")
    match = re.search(r"[\d.]+", str(value))
    return float(match.group()) if match else float("nan")


def parse_rating(value: str):
    if pd.isna(value):
        return float("nan")
    return RATING_WORDS.get(str(value).strip(), float("nan"))


def parse_in_stock(value: str):
    if pd.isna(value):
        return None
    return "in stock" in str(value).strip().lower()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_gbp"] = df["price"].apply(parse_price)
    df["rating"] = df["star_rating"].apply(parse_rating)
    df["in_stock"] = df["availability"].apply(parse_in_stock)

    before = len(df)
    df = df.dropna(subset=["price_gbp"])
    dropped_price = before - len(df)

    if df["rating"].isna().any():
        median_rating = int(round(df["rating"].median()))
        n_imputed = int(df["rating"].isna().sum())
        df["rating"] = df["rating"].fillna(median_rating)
        print(f"  imputed {n_imputed} missing rating value(s) with column median = {median_rating}")
    df["rating"] = df["rating"].astype(int)

    before = len(df)
    df = df.dropna(subset=["in_stock"])
    dropped_stock = before - len(df)
    df["in_stock"] = df["in_stock"].astype(bool)

    if dropped_price or dropped_stock:
        print(f"  dropped {dropped_price} row(s) with unparseable price, "
              f"{dropped_stock} row(s) with unparseable availability")

    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR_RATE).round(2)

    return df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]]


def main():
    raw = pd.read_csv(RAW_PATH)
    print(f"Loaded {len(raw)} raw rows from {RAW_PATH}")

    cleaned = clean(raw)
    cleaned.to_csv(CLEAN_PATH, index=False, encoding="utf-8")
    print(f"Cleaned {len(cleaned)} rows -> {CLEAN_PATH}")
    print(f"Conversion rate used: 1 GBP = {GBP_TO_INR_RATE} INR (fixed project baseline)")
    print(cleaned.dtypes)


if __name__ == "__main__":
    main()

"""
Module 1 - Step 3: Load the cleaned data into a normalized SQLite database.
"""
import os
import sqlite3
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CLEAN_PATH = os.path.join(DATA_DIR, "clean_books.csv")
DB_PATH = os.path.join(DATA_DIR, "zepto_books.db")

SCHEMA_SQL = """
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
);

CREATE TABLE books (
    book_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    price_gbp   REAL NOT NULL,
    price_inr   REAL NOT NULL,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    in_stock    INTEGER NOT NULL CHECK (in_stock IN (0, 1)),
    category_id INTEGER NOT NULL REFERENCES categories(category_id)
);
"""


def build(db_path: str = DB_PATH, clean_path: str = CLEAN_PATH):
    df = pd.read_csv(clean_path)
    df["in_stock"] = df["in_stock"].astype(bool)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)

        categories = sorted(df["category"].unique())
        cat_df = pd.DataFrame({"category_name": categories})
        cat_df.to_sql("categories", conn, if_exists="append", index=False)

        cat_id_map = pd.read_sql("SELECT category_id, category_name FROM categories", conn)
        cat_id_map = dict(zip(cat_id_map["category_name"], cat_id_map["category_id"]))

        books_df = df.copy()
        books_df["category_id"] = books_df["category"].map(cat_id_map)
        books_df["in_stock"] = books_df["in_stock"].astype(int)
        books_df = books_df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category_id"]]
        books_df.to_sql("books", conn, if_exists="append", index=False)

        conn.commit()

        n_cats = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        n_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        print(f"Loaded {n_cats} categories and {n_books} books into {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    build()

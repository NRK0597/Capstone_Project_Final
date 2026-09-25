"""
Module 1 - Step 4: Run required SQL queries against the SQLite database, read two of them back into pandas via pd.read_sql, and reproduce the JOIN
query purely with pd.merge on in-memory DataFrames to show equivalence.
"""
import os
import io
import sqlite3
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "zepto_books.db")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "queries_output.txt")

QUERIES = {
    "Q1: SELECT/WHERE - in-stock books priced under 20 GBP": """
        SELECT title, price_gbp, rating
        FROM books
        WHERE in_stock = 1 AND price_gbp < 20
        LIMIT 10;
    """,
    "Q2: ORDER BY + LIMIT - 10 most expensive books": """
        SELECT title, price_gbp
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 10;
    """,
    "Q3: DISTINCT - list of distinct categories": """
        SELECT DISTINCT category_name
        FROM categories
        ORDER BY category_name;
    """,
    "Q4: IN / BETWEEN - 4-5 star books priced between 20 and 40 GBP": """
        SELECT title, price_gbp, rating
        FROM books
        WHERE rating IN (4, 5) AND price_gbp BETWEEN 20 AND 40
        ORDER BY price_gbp;
    """,
    "Q5: JOIN - top 3 highest-rated books per category": """
        SELECT c.category_name, b.title, b.rating, b.price_gbp
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.book_id IN (
            SELECT b2.book_id
            FROM books b2
            WHERE b2.category_id = b.category_id
            ORDER BY b2.rating DESC, b2.price_gbp ASC
            LIMIT 3
        )
        ORDER BY c.category_name, b.rating DESC;
    """,
    "Q6: JOIN - average price and book count per category": """
        SELECT c.category_name,
               COUNT(b.book_id) AS num_books,
               ROUND(AVG(b.price_gbp), 2) AS avg_price_gbp,
               ROUND(AVG(b.price_inr), 2) AS avg_price_inr
        FROM categories c
        JOIN books b ON b.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY avg_price_gbp DESC;
    """,
    "Q7: JOIN - in-stock 5-star books with their category": """
        SELECT b.title, b.price_gbp, c.category_name
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.rating = 5 AND b.in_stock = 1
        ORDER BY c.category_name, b.price_gbp;
    """,
}


def run_all(conn: sqlite3.Connection, out):
    for label, sql in QUERIES.items():
        print(f"\n{'=' * 80}\n{label}\n{'=' * 80}", file=out)
        print(sql.strip(), file=out)
        df = pd.read_sql(sql, conn)
        print(f"\n-- {len(df)} row(s) --", file=out)
        print(df.to_string(index=False), file=out)
    return


def pandas_vs_sql_join(conn: sqlite3.Connection, out):
    print(f"\n{'=' * 80}\nQ8: pd.read_sql vs pd.merge equivalence check (JOIN query)\n{'=' * 80}", file=out)

    join_sql = """
        SELECT c.category_name, b.title, b.rating, b.price_gbp
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        ORDER BY c.category_name, b.title;
    """
    via_read_sql = pd.read_sql(join_sql, conn)

    books_df = pd.read_sql("SELECT * FROM books", conn)
    categories_df = pd.read_sql("SELECT * FROM categories", conn)
    via_merge = (
        pd.merge(books_df, categories_df, on="category_id", how="inner")
        [["category_name", "title", "rating", "price_gbp"]]
        .sort_values(["category_name", "title"])
        .reset_index(drop=True)
    )
    via_read_sql = via_read_sql.sort_values(["category_name", "title"]).reset_index(drop=True)

    are_equal = via_read_sql.equals(via_merge)
    print(f"\npd.read_sql result shape: {via_read_sql.shape}", file=out)
    print(f"pd.merge   result shape: {via_merge.shape}", file=out)
    print(f"\nDataFrames are equal: {are_equal}", file=out)
    print("\n-- pd.read_sql (first 5 rows) --", file=out)
    print(via_read_sql.head().to_string(index=False), file=out)
    print("\n-- pd.merge (first 5 rows) --", file=out)
    print(via_merge.head().to_string(index=False), file=out)

    assert are_equal, "pd.read_sql and pd.merge results do not match!"


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        buf = io.StringIO()
        run_all(conn, buf)
        pandas_vs_sql_join(conn, buf)
        text = buf.getvalue()
    finally:
        conn.close()

    print(text)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nFull query log written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

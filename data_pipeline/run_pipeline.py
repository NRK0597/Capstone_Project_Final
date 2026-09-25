"""
Module 1: runs the full data pipelines end to end.
"""
import scrape
import clean_transform
import build_database
import run_queries


def main():
    print("### Step 1/4: Scraping "books.toscrape.com" Website ###")
    scrape.main()

    print("\n### Step 2/4: DOing Cleaning + currency conversion in the scrapped data.###")
    clean_transform.main()

    print("\n### Step 3/4: Building normalized SQLite database on c###")
    build_database.build()

    print("\n### Step 4/4: Running SQL queries + pandas comparison ###")
    run_queries.main()

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
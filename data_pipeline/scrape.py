"""
Module 1 - Step 1: Scrapes every book across a fixed list of categories, and writes the raw, unmodified fields to data/raw_books.csv.
"""
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

BASE_URL = "http://books.toscrape.com/"
CATEGORY_TYPES = [
    "travel_2",
    "mystery_3",
    "historical-fiction_4",
    "sequential-art_5",
    "classics_6",
]
Output_DIr = os.path.join(os.path.dirname(__file__), "data")
Output_Path = os.path.join(Output_DIr, "raw_books.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (Capstone Project educational scraper)"}


def scrape_category(type: str) -> list[dict]:
    """Scrape every book in a category, following 'next' pagination links."""
    category_name = None
    rows = []
    url = f"{BASE_URL}catalogue/category/books/{type}/index.html"

    while url:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        if category_name is None:
            h1 = soup.select_one("div.page-header h1")
            category_name = h1.get_text(strip=True) if h1 else type

        for article in soup.select("article.product_pod"):
            title = article.h3.a["title"].strip()
            price_text = article.select_one("p.price_color").get_text(strip=True)
            rating_class = article.select_one("p.star-rating")["class"]
            # class list looks like ["star-rating", "Three"]
            star_rating = next((c for c in rating_class if c != "star-rating"), None)
            availability = article.select_one("p.instock.availability").get_text(strip=True)

            rows.append(
                {
                    "title": title,
                    "price": price_text,
                    "star_rating": star_rating,
                    "availability": availability,
                    "category": category_name,
                }
            )

        next_link = soup.select_one("li.next a")
        if next_link:
            base_dir = url.rsplit("/", 1)[0] + "/"
            url = base_dir + next_link["href"]
        else:
            url = None

        time.sleep(0.2)  # be polite to the sandbox server

    return rows


def main():
    os.makedirs(Output_DIr, exist_ok=True)
    all_rows = []
    for type in CATEGORY_TYPES:
        rows = scrape_category(type)
        print(f"  scraped {len(rows):3d} books from category type '{type}'")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df.to_csv(Output_Path, index=False)
    print(f"\nSaved {len(df)} raw book rows across {df['category'].nunique()} categories -> {Output_Path}")


if __name__ == "__main__":
    main()
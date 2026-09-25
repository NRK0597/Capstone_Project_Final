# Module 1-Data Pipeline

## What I did in this module

I built this small pipeline that scraps book data from a real website ([books.toscrape.com](http://books.toscrape.com)) given in the project, cleans it up, saves it in a database, and then asks that database some questions using SQL and pandas.

## What was expected

The task asked for:

- At least 60 books from at least 3 different categories should be collected without any manual copy pasting. For every book the columns the title, price, star rating, whether it is in stock, and its category needs to be scrapped. Then clean columns such as price as a number (price_gbp), star rating as a number from 1 to 5 (rating), and stock status as True/False (in_stock).
- A new column price_inr made by converting the GBP price using a fixed rate of 1 GBP = 105.50 INR.
- A database with two tables that are linked to each other (a primary key and a foreign key). At least 5 SQL queries, together covering SELECT/WHERE, ORDER BY, LIMIT, DISTINCT, IN/BETWEEN, and at least one JOIN. Reading some of the SQL results into pandas, and also doing the same join using pandas.merge() to check both give the same answer.

## What I got in the end:

- 163 books collected from 5 categories (Travel, Mystery, Historical Fiction, Sequential Art, Classics) with more than the 60 books / 3 categories. All the required columns (price_gbp, rating, in_stock, price_inr) present and in the correct format.
- A SQLite database (data/zepto_books.db) with two tables, categories and books, joined on category_id. 8 SQL queries in total, including 4 different queries that use JOIN.
- The pd.read_sql result and the pandas.merge() result for the join match exactly (163 rows, same columns, same values), which the script checks and prints out.

## How to set it up and run it

From the main project folder:

```bash
python -m venv .venv
.venv\Scripts\activate

pip install -r data_pipeline/requirements.txt
```

Then, to run everything from start to finish:

```bash
cd data_pipeline
python run_pipeline.py
```

This does 4 things, one after another:

1. scrape.py file visits the five categories on the website, follows the "next page" links inside each one, and saves everything into data/raw_books.csv.
2. clean_transform.py cleans the raw data and saves it as data/clean_books.csv.
3. build_database.py builds the SQLite database data/zepto_books.db from the cleaned data.
4. run_queries.py runs all the SQL queries and the pandas check, and saves the results in queries_output.txt.

We can also run each single file on its own.

## Problems I faced while doing this module.

When I first scraped the prices, instead of showing "£10.00" it showed something like "Â£10.00" with extra weird characters before the pound sign. After checking, I realised that page sending as UTF-8 text, so the requests library was guessing the wrong text format. I fixed this by telling requests directly to read the page as UTF-8 (resp.encoding = "utf-8") before reading any text from it. After this fix, the £ symbol showed correctly.

A few categories (like Mystery and Sequential Art) had more books than can be shown on a single page, so the website splits them across multiple pages with a "next" button. My first version of the scraper only grabbed the first page, so I was getting fewer books than expected for those categories. I fixed this by checking for a "next" link at the bottom of the page and, if it exists, following it and collecting more books, repeating until there is no "next" link left.

The task says that if a value cannot be cleaned, I should either drop that row or fill in the missing value. I decided: if the price or stock status cannot be read, I drop that row completely (because I cannot guess a book's price). If only the star rating cannot be read, I fill it in with the middle (median) rating instead of throwing away the whole row, since the rest of the row is still good data.

## How the price is converted to INR

**1 GBP = 105.50 INR** is a fixed rate that was mentioned to use for this project. I just multiply by this number directly inside clean_transform.py.

## Database schema

Two tables, linked with a primary key / foreign key saved as data/zepto_books.db:

```sql
categories(category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE)
books(book_id INTEGER PRIMARY KEY, title TEXT, price_gbp REAL, price_inr REAL, rating INTEGER, in_stock INTEGER, category_id INTEGER REFERENCES categories(category_id))
```

## SQL queries (run_queries.py, results saved in queries_output.txt)

| #  | Query                                     | What it shows            |
| -- | ----------------------------------------- | ------------------------ |
| Q1 | In-stock books under £20                 | SELECT / WHERE           |
| Q2 | 10 most expensive books                   | ORDER BY / LIMIT         |
| Q3 | Distinct category names                   | DISTINCT                 |
| Q4 | 4-5 star books priced £20-£40           | IN / BETWEEN             |
| Q5 | Top 3 highest-rated books per category    | JOIN (with a sub-query)  |
| Q6 | Average price and book count per category | JOIN + GROUP BY          |
| Q7 | In-stock 5-star books with their category | JOIN                     |
| Q8 | Full books-categories join, read two ways | pd.read_sql vs pd.merge  |

## Files in this folder

```
data_pipeline/
├── scrape.py             # Step 1: scraping
├── clean_transform.py    # Step 2: cleaning + currency conversion
├── build_database.py     # Step 3: SQLite schema + load
├── run_queries.py        # Step 4: SQL queries + pandas comparison
├── run_pipeline.py       # runs all 4 steps in order
├── requirements.txt
├── queries_output.txt    # saved output of run_queries.py
└── data/
    ├── raw_books.csv  
    ├── clean_books.csv  
    └── zepto_books.db   
```

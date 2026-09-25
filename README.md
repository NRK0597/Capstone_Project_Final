# Capstone Project - Zepto Data

```
DATA → ANALYSIS → ML → GENAI → API
```

| Module                 | Folder                                      | What it does                                                                                                                                                                                                  |
| ---------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 - Data Pipeline      | [`/data_pipeline`](data_pipeline/)         | This data pipeline scrapes the website books.toscrape.com then cleans it, converts currency as mentioned in the requirement then loads a normalized SQLite DB and queries it with SQL and pandas. |
| 2 - Analytics          | [`/analytics`](analytics/)                 | This module profiles and cleans the Titanic dataset which tells a visual data story, then builds/tunes/evaluates a full classification and regression modeling pipeline.                       |
| 3 - Support Assistant | [`/support_assistant`](support_assistant/) | This is a RAG assistant over Zepto's own policy docs provided in the project - ChromaDB + sentence - transformers + LangGraph + FastAPI, deterministic/offline by default.                                   |

Each module has its own detailed README with design decisions, results, and exact run instructions and this root README covers setup of the complete project which tells how to run everything from end to end, and a short summary of each module.

## Repository structure

```
Capstone Project/
├─ data_pipeline/       # Module 1
├─ analytics/           # Module 2
├─ support_assistant/   # Module 3
└─ README.md            # this file
```

## Setup

Each module has its own requirements.txt file. Running the below to create the virtual environment and then can install all three if want to run everything without switching environments:

```bash
python -m venv .venv
.venv\Scripts\activate

pip install -r data_pipeline/requirements.txt
pip install -r analytics/requirements.txt
pip install -r support_assistant/requirements.txt
```

Or install/activate a fresh environment per module if separate venv is needed.

## Running each module end to end

### Module 1-Data Pipeline

```bash
cd data_pipeline
python run_pipeline.py
```

Running this Scrapes ≥60 books across 5 categories from the website "books.toscrape.com" and then cleans/types the fields, converts the currency GBP to INR at the fixed project rate (1 GBP = 105.50 INR), then builds a normalized two-table SQLite database (data/zepto_books.db), and runs 6 SQL queries (covering SELECT/WHERE, ORDER BY/LIMIT, DISTINCT, IN/BETWEEN, and a JOIN), printing and saving results to "queries_output.txt" file, including a "pd.read_sql" vs. "pd.merge" equivalence check. For full details and cleaning decisions can refer to the file `data_pipeline/README.md`.

### Module 2-Analytics + ML

```bash
cd analytics
jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_modeling.ipynb
```

For the module 2, "01_eda.ipynb" loads the Titanic dataset, profiles it, cleans it, and produces the full EDA data story. "02_modeling.ipynb" reads that generated "titanic.csv", builds a model pipeline, trains/compares 3 classifiers, handles class imbalance, tunes and runs a regression side task, and saves the final deployable pipeline to "titanic_pipeline.joblib". Both notebooks are committed with their outputs already executed. Refer to the file [`analytics/README.md`](analytics/README.md) for every result, metric, and written interpretation.

### Module 3-Support Assistant

```bash
cd support_assistant
python ingest.py                          
uvicorn main:app --host 0.0.0.0 --port 7860
```

Then POST a query to http://localhost:7860/ask or run it containerized by running the below:

```bash
cd support_assistant
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

Graded with MOCK_LLM left at its default. See [`support_assistant/README.md`](support_assistant/README.md) for the full pipeline architecture information, example request/response transcripts, and the optional real-LLM extension.

## Design decisions with summary per module:

**Module 1 (Data Pipeline).** The website "books.toscrape.com" sends its pages as UTF-8 but doesn't say so, so the "£" symbol comes out wrong unless I set the encoding manually and I handled that in "scrape.py". If a book's price or stock status can't be read properly, I just drop that row, since there's no good way to guess those values. If only the rating is bad, I fill it in with the median rating instead, since the rest of the row is still fine to keep. For currency, I only used the fixed rate given in the requirements (1 GBP = 105.50 INR). The database is simple with the two tables, categories and books, linked by a primary key/foreign key.

**Module 2 (Analytics + ML).** I split the work into two notebooks that don't share any Python state and the notebooks are "01_eda.ipynb" and "02_modeling.ipynb". The only thing which is common and passed between them is the saved titanic.csv file, which also conveniently satisfies the requirement of loading the raw data. In the EDA notebook I used simple, quick cleaning (filled missing age with the median, dropped 2 rows missing embarked, dropped the deck column since it was 77% missing). In the modeling notebook I used a stricter, more proper approach with a ColumnTransformer that only learns from the training data. For the final model, I picked the tuned Random Forest over Logistic Regression, even though Logistic Regression had a slightly higher AUC, because the Random Forest was more consistent.

**Module 3 (Support Assistant).** Each policy document is short, so I treated one whole document as one chunk. I used MOCK_LLM only at the two places that would otherwise need a real LLM call for generating the final answer in retrieve_and_answer, and the entire direct_answer function. Everything else (ingestion, embeddings, retrieval, and the LangGraph routing logic) always runs for real regardless of MOCK_LLM, so the requirement that "retrieval always runs for real" is satisfied naturally by how the code is structured.

# Velora Brewing - End-to-End Data Science Project

Synthetic brewery dataset (fictional Slovenian brewery, 13 beers, 2023-2026, EUR).
Goal: Excel -> Python -> SQL -> EDA -> Cleaning -> Statistics -> ML -> NLP/GenAI -> Streamlit.

> The data is synthetic and for education only. It is not real brewery data.

## Project structure
    data/raw/         original Excel file (never edit this)
    data/processed/   cleaned data (created later)
    notebooks/        Jupyter notebooks
    src/              reusable Python code
    sql/              SQL queries
    app/              Streamlit dashboard
    reports/          validation report, EDA report

## How to run
    pip install -r requirements.txt
    python src/load_data.py        # load all sheets
    python src/validate_data.py    # run 6 quality checks -> reports/validation_report.txt

## Progress
- [x] Step 1: Project setup
- [x] Step 2: Load and validate data
- [ ] Step 3: SQL database

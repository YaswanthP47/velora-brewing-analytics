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

## Known data issues (found in Step 2 validation)

1. **Supplier on-time rate conflict.** The Suppliers sheet states about 90%,
   but calculating from Procurement_Orders (actual vs expected delivery)
   gives about 43%. I use the calculated value, following the KPI_Glossary formula.
2. **Customer first_order_date is unreliable.** About 52% of orders happen
   before the customer's stated first_order_date. I derive it from Sales_Orders instead.

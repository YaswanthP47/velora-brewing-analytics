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
    python src/load_data.py                   # load all sheets
    python src/validate_data.py               # run 6 quality checks -> reports/validation_report.txt
    python src/build_database.py              # build SQLite database -> data/velora.db
    python src/run_queries.py                 # run 20 SQL queries -> reports/sql_results/
    python src/generate_docs.py               # create docs/ (dictionary, KPIs, data model)
    python src/generate_synthetic_data.py     # create synthetic CSVs in data/synthetic/

## Progress

- [x] Step 1: Project setup
- [x] Step 2: Load and validate data
- [x] Step 3: SQL database
- [x] Step 4: Documentation and synthetic data generator

## Known data issues (found in Step 2 validation)

1. **Supplier on-time rate conflict.** The Suppliers sheet states about 90%,
   but calculating from Procurement_Orders (actual vs expected delivery)
   gives about 43%. I use the calculated value, following the KPI_Glossary formula.
2. **Customer first_order_date is unreliable.** About 52% of orders happen
   before the customer's stated first_order_date. I derive it from Sales_Orders instead.

## SQL Analysis (Step 3)

The Excel data is loaded into a SQLite database (`data/velora.db`).
20 business queries are in [sql/queries.sql](sql/queries.sql); results are saved
as CSV files in `reports/sql_results/`.
Techniques used: JOIN, GROUP BY, CASE WHEN, CTEs and window functions (LAG, RANK, moving average).
Cancelled orders are excluded from all revenue figures.

### Key findings

- **Revenue and margin:** net sales of about EUR 6.77 million with a 66.0% gross margin.
- **Top products:** Royal Reserve, Midnight Stout and Alpine IPA lead on revenue.
- **Discounts hurt margin:** margin falls from 68.3% (0-5% discount) to 63.0% (15%+ discount).
- **Suppliers:** calculated on-time delivery rates (33%-57%) are far below the rates
  stated in the Suppliers sheet (84%-97%).

### Example result

<!-- ![Revenue by product](images/q03_revenue_by_product.png) -->

### Data limitations

- Inventory movements have no opening stock, so absolute stock levels cannot be calculated.
- Monthly expenses exceed gross profit in every month of this synthetic dataset.
- 2026 contains data only up to October, so year-on-year comparison needs care.

## Documentation (Step 4)

- [Data dictionary](docs/data_dictionary.md): all 17 tables and 134 columns
- [KPI definitions](docs/kpi_definitions.md): formulas, SQL and current values
- [Data model, assumptions and known issues](docs/data_model.md)
- Reproducible generator: `python src/generate_synthetic_data.py --seed 42`

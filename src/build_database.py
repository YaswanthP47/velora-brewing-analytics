"""
build_database.py  -  STEP 3a: Turn the Excel data into a SQLite database.

Run from the project folder:
        python src/build_database.py

What it does:
    1. Loads the 17 data sheets (using load_data.py)
    2. Converts dates to text like '2025-03-14' (SQLite has no date type)
    3. Writes each sheet as a table inside  data/velora.db
    4. Creates indexes (they make joins and filters much faster)
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from load_data import load_data_tables  # noqa: E402

DB_FILE = Path("data/velora.db")

# Columns that should be searched/joined often -> we add an index on each.
INDEXES = {
    "Sales_Orders": ["customer_id", "distributor_id", "order_date", "order_status"],
    "Sales_Order_Lines": ["order_id", "product_id"],
    "Production_Batches": ["product_id", "production_date"],
    "Quality_Control": ["batch_id"],
    "Procurement_Orders": ["supplier_id", "material_id", "order_date"],
    "Inventory_Movements": ["product_id", "movement_date"],
    "Customer_Feedback": ["customer_id", "product_id"],
    "Demand_History": ["product_id", "month"],
}


def main():
    tables = load_data_tables()

    # Start fresh each time, so running the script twice never duplicates data.
    DB_FILE.parent.mkdir(exist_ok=True)
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(DB_FILE)

    for name, df in tables.items():
        df = df.copy()
        # Turn every date column into 'YYYY-MM-DD' text.
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d")
        df.to_sql(name, conn, index=False)
        print(f"  table {name:<22} {len(df):>6} rows written")

    for table, cols in INDEXES.items():
        for col in cols:
            conn.execute(f"CREATE INDEX idx_{table}_{col} ON {table}({col})")
    conn.commit()
    conn.close()
    print(f"\nDatabase created: {DB_FILE}  ({DB_FILE.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

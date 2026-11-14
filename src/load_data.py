"""
load_data.py  -  STEP 2a: Load the Excel file into Python.

What this file does:
    Reads EVERY sheet of the Velora Excel workbook and returns them
    as a Python dictionary:  { "Sheet_Name": DataFrame, ... }

A DataFrame is just a table (rows and columns), like an Excel sheet inside Python.
"""

from pathlib import Path
import pandas as pd

# Path to the Excel file, relative to the project folder.
DATA_FILE = Path("data/raw/Velora_Brewing_End_to_End_Data_Science_Dataset.xlsx")

# These 4 sheets are instructions/documentation, NOT business data.
DOC_SHEETS = ["START_HERE", "Learning_Roadmap", "KPI_Glossary", "Data_Dictionary"]


def load_all_sheets(path=DATA_FILE):
    """Return a dict with one DataFrame per sheet."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Could not find {path}. Did you copy the Excel file into data/raw/ ?"
        )
    # sheet_name=None  ->  read ALL sheets at once
    return pd.read_excel(path, sheet_name=None)


def load_data_tables(path=DATA_FILE):
    """Return only the business-data sheets (skips the 4 documentation sheets)."""
    sheets = load_all_sheets(path)
    return {name: df for name, df in sheets.items() if name not in DOC_SHEETS}


if __name__ == "__main__":
    tables = load_data_tables()
    print(f"Loaded {len(tables)} data tables:\n")
    for name, df in tables.items():
        print(f"  {name:<22} {df.shape[0]:>6} rows  x {df.shape[1]:>2} columns")

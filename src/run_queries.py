"""
run_queries.py  -  STEP 3b: Run every query in sql/queries.sql and show results.

Run from the project folder:
        python src/run_queries.py          # run all queries
        python src/run_queries.py 3        # run only Q3

Results are also saved as CSV files in reports/sql_results/
"""

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

DB_FILE = Path("data/velora.db")
SQL_FILE = Path("sql/queries.sql")
OUT_DIR = Path("reports/sql_results")


def read_queries():
    """Split queries.sql into {number: (title, sql_text)} using the '-- Q<n>:' markers."""
    text = SQL_FILE.read_text(encoding="utf-8")
    parts = re.split(r"^-- Q(\d+): (.*)$", text, flags=re.MULTILINE)
    queries = {}
    for i in range(1, len(parts), 3):
        number, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        sql = body.split("-- ====")[0].strip()   # drop any trailing comment banner
        queries[number] = (title, sql)
    return queries


def main():
    if not DB_FILE.exists():
        sys.exit("data/velora.db not found. Run:  python src/build_database.py")

    queries = read_queries()
    wanted = [int(a) for a in sys.argv[1:]] or sorted(queries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200, "display.max_columns", 20)

    conn = sqlite3.connect(DB_FILE)
    for n in wanted:
        title, sql = queries[n]
        print("\n" + "=" * 78)
        print(f"Q{n}: {title}")
        print("=" * 78)
        df = pd.read_sql_query(sql, conn)
        print(df.to_string(index=False))
        df.to_csv(OUT_DIR / f"Q{n:02d}.csv", index=False)
    conn.close()
    print(f"\nCSV results saved in {OUT_DIR}/")


if __name__ == "__main__":
    main()

import pandas as pd
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from data_generator import generate_sales, generate_support, generate_marketing, save_to_sqlite
from anomaly_detector import run_detection
from report_generator import generate_report


def load_data():
    db = "data/raw/business.db"
    if not os.path.exists(db):
        print("no data found — generating...")
        s = generate_sales()
        sup = generate_support()
        m = generate_marketing()
        save_to_sqlite(s, sup, m)

    conn = sqlite3.connect(db)
    sales = pd.read_sql("SELECT * FROM sales", conn, parse_dates=["date"])
    support = pd.read_sql("SELECT * FROM support", conn, parse_dates=["date"])
    marketing = pd.read_sql("SELECT * FROM marketing", conn, parse_dates=["date"])
    conn.close()
    return sales, support, marketing


if __name__ == "__main__":
    print("=" * 55)
    print("  BI ANOMALY ENGINE")
    print("=" * 55)

    sales, support, marketing = load_data()
    print(f"loaded: {len(sales)} sales | {len(support)} support | {len(marketing)} marketing rows")

    anomalies = run_detection(sales, support, marketing)

    path = generate_report(sales, support, marketing, anomalies)

    print("=" * 55)
    print(f"done. open: {path}")
    print("=" * 55)

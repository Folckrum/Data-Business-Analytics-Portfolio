import pandas as pd
import numpy as np
import sqlite3
import json
import os
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/pipeline.log")]
)
log = logging.getLogger(__name__)

Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)

DB = "data_warehouse.db"
np.random.seed(1)


def extract_customers(n=2000):
    log.info("extracting customers...")
    cities = ["Mumbai","Delhi","Bangalore","Pune","Chennai","Hyderabad","Kolkata"]
    segs = ["Retail","Wholesale","Premium","New"]
    df = pd.DataFrame({
        "customer_id": [f"CUST{i:05d}" for i in range(1, n+1)],
        "name": [f"Customer_{i}" for i in range(1, n+1)],
        "email": [f"user{i}@example.com" for i in range(1, n+1)],
        "city": np.random.choice(cities, n),
        "segment": np.random.choice(segs, n),
        "signup_date": pd.to_datetime(np.random.choice(pd.date_range("2020-01-01","2023-12-31"), n)).astype(str),
        "is_active": np.random.choice([True, False], n, p=[0.85, 0.15]),
        "credit_limit": np.random.choice([5000, 10000, 25000, 50000], n),
    })
    df.loc[df.sample(50).index, "email"] = None
    df.loc[df.sample(30).index, "city"] = "Unknown"
    df.to_csv("data/raw/customers.csv", index=False)
    log.info(f"extracted {len(df)} customers")
    return df


def extract_orders(n=15000):
    log.info("extracting orders...")
    cats = ["Electronics","Clothing","Furniture","Food","Sports","Books"]
    statuses = ["Completed","Shipped","Cancelled","Returned","Pending"]
    cids = [f"CUST{i:05d}" for i in range(1, 2001)]
    df = pd.DataFrame({
        "order_id": [f"ORD{i:07d}" for i in range(1, n+1)],
        "customer_id": np.random.choice(cids, n),
        "order_date": pd.to_datetime(np.random.choice(pd.date_range("2023-01-01","2023-12-31"), n)).astype(str),
        "category": np.random.choice(cats, n),
        "quantity": np.random.randint(1, 20, n),
        "unit_price": np.random.uniform(10, 2000, n).round(2),
        "discount_pct": np.random.choice([0, 5, 10, 15, 20], n),
        "status": np.random.choice(statuses, n, p=[0.60, 0.20, 0.08, 0.07, 0.05]),
        "warehouse_id": np.random.choice(["WH01","WH02","WH03"], n),
    })
    df.loc[df.sample(100).index, "unit_price"] = None
    dups = df.sample(50)
    df = pd.concat([df, dups], ignore_index=True)
    df.to_csv("data/raw/orders.csv", index=False)
    log.info(f"extracted {len(df)} orders ({len(dups)} injected dups)")
    return df


def extract_products(n=500):
    log.info("extracting products...")
    cats = ["Electronics","Clothing","Furniture","Food","Sports","Books"]
    brands = ["BrandA","BrandB","BrandC","BrandD","BrandE"]
    products = [{
        "product_id": f"PROD{i:05d}",
        "name": f"Product_{i}",
        "category": np.random.choice(cats),
        "brand": np.random.choice(brands),
        "cost_price": round(float(np.random.uniform(5, 800)), 2),
        "list_price": round(float(np.random.uniform(10, 2000)), 2),
        "stock_qty": int(np.random.randint(0, 500)),
        "is_active": bool(np.random.choice([True, False], p=[0.90, 0.10])),
    } for i in range(1, n+1)]
    with open("data/raw/products.json", "w") as f:
        json.dump(products, f, indent=2)
    log.info(f"extracted {n} products")
    return pd.DataFrame(products)


def transform_customers(df):
    log.info("transforming customers...")
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"])
    df["email"] = df["email"].fillna("no-email@unknown.com")
    df["city"] = df["city"].replace("Unknown", "Not Specified")
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["tenure_days"] = (pd.Timestamp("2024-01-01") - df["signup_date"]).dt.days
    df["segment"] = df["segment"].str.strip().str.title()
    df.to_csv("data/processed/customers_clean.csv", index=False)
    log.info(f"customers: {before} → {len(df)}")
    return df


def transform_orders(df):
    log.info("transforming orders...")
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["gross_revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["net_revenue"] = (df["gross_revenue"] * (1 - df["discount_pct"]/100)).round(2)
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["is_completed"] = (df["status"] == "Completed").astype(int)
    df["is_returned"] = (df["status"] == "Returned").astype(int)
    df.to_csv("data/processed/orders_clean.csv", index=False)
    log.info(f"orders: {before} → {len(df)} (deduped, nulls filled)")
    return df


def transform_products(df):
    log.info("transforming products...")
    df = df.drop_duplicates(subset=["product_id"])
    df["margin_pct"] = ((df["list_price"] - df["cost_price"]) / df["list_price"] * 100).round(2)
    df["price_tier"] = pd.cut(df["list_price"], bins=[0,100,500,1000,float("inf")],
                               labels=["Budget","Mid-range","Premium","Luxury"])
    df["is_low_stock"] = (df["stock_qty"] < 20).astype(int)
    df.to_csv("data/processed/products_clean.csv", index=False)
    log.info(f"products: {len(df)} records")
    return df


def load(customers, orders, products):
    log.info(f"loading to {DB}...")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS dim_customers (
            customer_id TEXT PRIMARY KEY, name TEXT, email TEXT, city TEXT,
            segment TEXT, signup_date TEXT, is_active INTEGER,
            credit_limit REAL, tenure_days INTEGER
        );
        CREATE TABLE IF NOT EXISTS dim_products (
            product_id TEXT PRIMARY KEY, name TEXT, category TEXT, brand TEXT,
            cost_price REAL, list_price REAL, stock_qty INTEGER,
            is_active INTEGER, margin_pct REAL, price_tier TEXT, is_low_stock INTEGER
        );
        CREATE TABLE IF NOT EXISTS fact_orders (
            order_id TEXT PRIMARY KEY, customer_id TEXT, order_date TEXT,
            category TEXT, quantity INTEGER, unit_price REAL, discount_pct REAL,
            gross_revenue REAL, net_revenue REAL, status TEXT, warehouse_id TEXT,
            order_month TEXT, order_quarter TEXT, is_completed INTEGER, is_returned INTEGER
        );
        CREATE TABLE IF NOT EXISTS etl_audit (
            run_id TEXT, table_name TEXT, rows INTEGER, loaded_at TEXT
        );
    """)
    conn.commit()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
    products.to_sql("dim_products", conn, if_exists="replace", index=False)
    orders.to_sql("fact_orders", conn, if_exists="replace", index=False)

    cur.executemany("INSERT INTO etl_audit VALUES (?,?,?,?)", [
        (run_id, "dim_customers", len(customers), datetime.now().isoformat()),
        (run_id, "dim_products", len(products), datetime.now().isoformat()),
        (run_id, "fact_orders", len(orders), datetime.now().isoformat()),
    ])
    conn.commit()

    print("\nValidation:")
    for label, q in [
        ("customers", "SELECT COUNT(*) FROM dim_customers"),
        ("orders", "SELECT COUNT(*) FROM fact_orders"),
        ("revenue", "SELECT ROUND(SUM(net_revenue),2) FROM fact_orders WHERE is_completed=1"),
        ("null prices", "SELECT COUNT(*) FROM fact_orders WHERE unit_price IS NULL"),
    ]:
        print(f"  {label}: {conn.execute(q).fetchone()[0]:,}")

    conn.close()
    log.info(f"load complete | run_id={run_id}")


if __name__ == "__main__":
    start = datetime.now()
    log.info("pipeline started")

    load(
        transform_customers(extract_customers()),
        transform_orders(extract_orders()),
        transform_products(extract_products()),
    )

    log.info(f"pipeline done in {(datetime.now()-start).total_seconds():.2f}s")

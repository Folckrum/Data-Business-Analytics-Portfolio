import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import json
import os

np.random.seed(0)

CATEGORIES = ["Electronics", "Clothing", "Furniture", "Sports", "Books"]
REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Online", "Retail", "App"]

os.makedirs("data/raw", exist_ok=True)


def base_revenue(date, category):
    day = date.timetuple().tm_yday
    weekday = date.weekday()
    cat_base = {"Electronics": 120000, "Clothing": 80000, "Furniture": 60000, "Sports": 50000, "Books": 30000}
    seasonal = 1 + 0.3 * np.sin(2 * np.pi * day / 365)
    weekend = 1.25 if weekday >= 5 else 1.0
    return cat_base[category] * seasonal * weekend


def generate_sales(start="2024-01-01", end="2024-12-31"):
    dates = pd.date_range(start, end)
    rows = []
    for date in dates:
        for cat in CATEGORIES:
            for region in REGIONS:
                rev = base_revenue(date, cat) * np.random.uniform(0.85, 1.15) / len(REGIONS)
                orders = int(rev / np.random.uniform(800, 1200))
                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "category": cat,
                    "region": region,
                    "channel": np.random.choice(CHANNELS, p=[0.50, 0.30, 0.20]),
                    "revenue": round(rev, 2),
                    "orders": orders,
                    "units": orders * np.random.randint(1, 4),
                    "returns": int(orders * np.random.uniform(0.03, 0.12)),
                    "new_customers": int(orders * np.random.uniform(0.10, 0.25)),
                })
    df = pd.DataFrame(rows)

    # inject real anomalies for the engine to catch
    # 1. revenue crash — Electronics, North, last 7 days
    crash_mask = (df["date"] >= "2024-12-20") & (df["category"] == "Electronics") & (df["region"] == "North")
    df.loc[crash_mask, "revenue"] *= 0.32

    # 2. returns spike — Clothing, South, October
    spike_mask = (df["date"] >= "2024-10-10") & (df["date"] <= "2024-10-20") & \
                 (df["category"] == "Clothing") & (df["region"] == "South")
    df.loc[spike_mask, "returns"] = (df.loc[spike_mask, "orders"] * 0.45).astype(int)

    # 3. order volume anomaly — Sports, all regions, March (promo spike)
    promo_mask = (df["date"] >= "2024-03-15") & (df["date"] <= "2024-03-22") & (df["category"] == "Sports")
    df.loc[promo_mask, "orders"] = (df.loc[promo_mask, "orders"] * 2.8).astype(int)
    df.loc[promo_mask, "revenue"] *= 2.4

    # 4. new customer acquisition drop — App channel, Q2
    acq_mask = (df["date"] >= "2024-04-01") & (df["date"] <= "2024-06-30") & (df["channel"] == "App")
    df.loc[acq_mask, "new_customers"] = (df.loc[acq_mask, "new_customers"] * 0.4).astype(int)

    df.to_csv("data/raw/sales.csv", index=False)
    print(f"sales: {len(df)} rows | anomalies injected: 4")
    return df


def generate_support(start="2024-01-01", end="2024-12-31"):
    dates = pd.date_range(start, end)
    rows = []
    for date in dates:
        base_tickets = int(np.random.normal(120, 20))
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "tickets_opened": max(base_tickets, 0),
            "tickets_resolved": max(int(base_tickets * np.random.uniform(0.70, 0.95)), 0),
            "avg_resolution_hrs": round(np.random.uniform(4, 28), 1),
            "escalations": int(np.random.poisson(3)),
            "csat_score": round(np.random.uniform(3.2, 4.8), 2),
        })
    df = pd.DataFrame(rows)

    # support spike during Electronics crash
    crash_supp = (df["date"] >= "2024-12-20")
    df.loc[crash_supp, "tickets_opened"] = (df.loc[crash_supp, "tickets_opened"] * 3.1).astype(int)
    df.loc[crash_supp, "escalations"] = (df.loc[crash_supp, "escalations"] * 4).astype(int)
    df.loc[crash_supp, "csat_score"] = (df.loc[crash_supp, "csat_score"] * 0.65).round(2)

    df.to_csv("data/raw/support.csv", index=False)
    print(f"support: {len(df)} rows")
    return df


def generate_marketing(start="2024-01-01", end="2024-12-31"):
    dates = pd.date_range(start, end)
    rows = []
    for date in dates:
        spend = round(np.random.uniform(8000, 25000), 2)
        clicks = int(spend * np.random.uniform(8, 18))
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "ad_spend": spend,
            "impressions": clicks * int(np.random.uniform(5, 15)),
            "clicks": clicks,
            "conversions": int(clicks * np.random.uniform(0.02, 0.08)),
            "cpc": round(spend / max(clicks, 1), 4),
            "roas": round(np.random.uniform(2.5, 6.0), 2),
        })
    df = pd.DataFrame(rows)

    # App channel acquisition drop mirrors marketing spend cut Q2
    q2 = (df["date"] >= "2024-04-01") & (df["date"] <= "2024-06-30")
    df.loc[q2, "ad_spend"] *= 0.45
    df.loc[q2, "conversions"] = (df.loc[q2, "conversions"] * 0.40).astype(int)

    df.to_csv("data/raw/marketing.csv", index=False)
    print(f"marketing: {len(df)} rows")
    return df


def save_to_sqlite(sales, support, marketing):
    conn = sqlite3.connect("data/raw/business.db")
    sales.to_sql("sales", conn, if_exists="replace", index=False)
    support.to_sql("support", conn, if_exists="replace", index=False)
    marketing.to_sql("marketing", conn, if_exists="replace", index=False)
    conn.close()
    print("saved to data/raw/business.db")


if __name__ == "__main__":
    print("generating data...")
    s = generate_sales()
    sup = generate_support()
    m = generate_marketing()
    save_to_sqlite(s, sup, m)
    print("done")

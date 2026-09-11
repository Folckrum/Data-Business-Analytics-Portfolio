import pandas as pd
import numpy as np
import json
import os
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

BASE = Path("data")
RAW     = BASE / "raw"
CURATED = BASE / "curated"
SERVING = BASE / "serving"

for layer in [RAW, CURATED, SERVING]:
    for domain in ["orders", "customers", "products"]:
        (layer / domain).mkdir(parents=True, exist_ok=True)

np.random.seed(42)
cats = ["Electronics","Clothing","Furniture","Books","Sports"]
statuses = ["placed","confirmed","shipped","delivered","cancelled","returned"]
warehouses = ["WH_NORTH","WH_SOUTH","WH_EAST","WH_WEST"]
sources = ["mobile_app","web","retail_pos"]


def ingest_raw(n=10000, batch_date="2024-01-15"):
    log.info(f"ingesting raw orders | date={batch_date}")
    partition = f"year={batch_date[:4]}/month={batch_date[5:7]}/day={batch_date[8:10]}"
    out = RAW / "orders" / partition
    out.mkdir(parents=True, exist_ok=True)

    records = []
    for i in range(n):
        records.append({
            "event_id": f"EVT{i:08d}",
            "event_type": "order_placed",
            "ts": f"{batch_date}T{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}:00Z",
            "payload": {
                "order_id": f"ORD{np.random.randint(100000,999999)}",
                "customer_id": f"CUST{np.random.randint(1,5000):05d}",
                "category": np.random.choice(cats),
                "quantity": int(np.random.randint(1, 10)),
                "unit_price": round(float(np.random.uniform(50, 3000)), 2),
                "status": np.random.choice(statuses, p=[0.20,0.25,0.20,0.25,0.05,0.05]),
                "warehouse": np.random.choice(warehouses),
                "source": np.random.choice(sources),
            }
        })

    with open(out / "orders.json", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    log.info(f"raw: {n} events → {out}/orders.json")
    return records


def curate(batch_date="2024-01-15"):
    log.info(f"curating | date={batch_date}")
    partition = f"year={batch_date[:4]}/month={batch_date[5:7]}/day={batch_date[8:10]}"
    raw_file = RAW / "orders" / partition / "orders.json"

    rows = []
    with open(raw_file) as f:
        for line in f:
            e = json.loads(line)
            p = e["payload"]
            rows.append({
                "event_id": e["event_id"],
                "event_ts": pd.to_datetime(e["ts"]),
                "order_id": p["order_id"],
                "customer_id": p["customer_id"],
                "category": p["category"],
                "quantity": p["quantity"],
                "unit_price": p["unit_price"],
                "status": p["status"],
                "warehouse": p["warehouse"],
                "source": p["source"],
                "batch_date": batch_date,
            })

    df = pd.DataFrame(rows)
    before = len(df)
    df = df.drop_duplicates(subset=["event_id"])
    df["gross_revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["is_completed"] = (df["status"] == "delivered").astype(int)
    df["is_cancelled"] = (df["status"] == "cancelled").astype(int)
    df["is_returned"] = (df["status"] == "returned").astype(int)

    out = CURATED / "orders" / partition
    out.mkdir(parents=True, exist_ok=True)
    pq = out / "orders.parquet"
    df.to_parquet(pq, index=False, engine="pyarrow")
    log.info(f"curated: {before} → {len(df)} rows | {pq.stat().st_size/1024:.1f} KB")
    return df


def build_serving(df):
    log.info("building serving layer...")

    daily_cat = df.groupby(["batch_date","category"]).agg(
        total_orders=("order_id","count"),
        units=("quantity","sum"),
        revenue=("gross_revenue","sum"),
        completed=("is_completed","sum"),
        returned=("is_returned","sum"),
        aov=("gross_revenue","mean"),
    ).reset_index().round(2)
    daily_cat["completion_rate"] = (daily_cat["completed"] / daily_cat["total_orders"] * 100).round(2)
    daily_cat["return_rate"] = (daily_cat["returned"] / daily_cat["total_orders"] * 100).round(2)

    wh = df.groupby("warehouse").agg(
        orders=("order_id","count"),
        revenue=("gross_revenue","sum"),
        completed=("is_completed","sum"),
    ).reset_index()
    wh["completion_rate"] = (wh["completed"] / wh["orders"] * 100).round(2)

    ch = df.groupby("source").agg(
        orders=("order_id","count"),
        revenue=("gross_revenue","sum"),
    ).reset_index()
    ch["revenue_pct"] = (ch["revenue"] / ch["revenue"].sum() * 100).round(2)

    for data, name in [(daily_cat,"daily_category"), (wh,"warehouse_perf"), (ch,"channel_attr")]:
        out = SERVING / "orders" / name
        out.mkdir(parents=True, exist_ok=True)
        data.to_parquet(out / f"{name}.parquet", index=False)
        log.info(f"serving/{name}: {len(data)} rows")

    return daily_cat, wh, ch


if __name__ == "__main__":
    batch = "2024-01-15"
    log.info("data lake pipeline start")

    ingest_raw(n=10000, batch_date=batch)
    df = curate(batch_date=batch)
    daily, wh, ch = build_serving(df)

    print("\nCategory summary:")
    print(daily[["category","total_orders","revenue","return_rate"]].to_string(index=False))
    print("\nWarehouse performance:")
    print(wh[["warehouse","orders","completion_rate"]].to_string(index=False))
    print("\nChannel attribution:")
    print(ch[["source","orders","revenue_pct"]].to_string(index=False))

    print("\nLayer sizes:")
    for layer, name in [(RAW,"Raw (Bronze)"), (CURATED,"Curated (Silver)"), (SERVING,"Serving (Gold)")]:
        size = sum(f.stat().st_size for f in layer.rglob("*") if f.is_file())
        print(f"  {name}: {size/1024:.1f} KB")

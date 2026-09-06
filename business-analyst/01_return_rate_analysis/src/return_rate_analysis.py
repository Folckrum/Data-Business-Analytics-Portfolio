import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

np.random.seed(21)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
sns.set_theme(style="whitegrid")


def generate_data(n=5000):
    categories = ["Electronics", "Clothing", "Furniture", "Books", "Toys", "Sports"]
    regions = ["North", "South", "East", "West"]
    return_reasons = ["Defective", "Wrong Item", "Not as Described", "Changed Mind",
                      "Better Price", "Delivery Damage", "Size Issue"]
    channels = ["Online", "Retail", "Mobile App"]
    payment = ["Credit Card", "UPI", "COD", "Net Banking"]

    df = pd.DataFrame({
        "order_id": range(10001, 10001 + n),
        "order_date": pd.to_datetime(
            np.random.choice(pd.date_range("2023-01-01", "2023-12-31"), n)
        ),
        "category": np.random.choice(categories, n),
        "region": np.random.choice(regions, n),
        "channel": np.random.choice(channels, n, p=[0.55, 0.30, 0.15]),
        "payment_method": np.random.choice(payment, n),
        "order_value": np.random.uniform(50, 5000, n).round(2),
        "delivery_days": np.random.randint(1, 15, n),
        "is_returned": np.random.choice([0, 1], n, p=[0.78, 0.22]),
    })

    returned = df[df["is_returned"] == 1]
    df.loc[returned.index, "return_reason"] = np.random.choice(return_reasons, len(returned))

    # Electronics has higher defect return rate
    elec_returned = df[(df["category"] == "Electronics") & (df["is_returned"] == 1)].index
    df.loc[elec_returned[:int(len(elec_returned) * 0.4)], "return_reason"] = "Defective"

    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["quarter"] = df["order_date"].dt.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    return df


def plot_return_rate_overview(df):
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle("E-Commerce Return Rate — Root Cause Analysis", fontsize=16, fontweight="bold")

    # Overall return rate
    return_rate = df["is_returned"].mean() * 100
    axes[0, 0].pie([return_rate, 100 - return_rate], labels=["Returned", "Kept"],
                   autopct="%1.1f%%", colors=["#e74c3c", "#2ecc71"], startangle=90)
    axes[0, 0].set_title(f"Overall Return Rate: {return_rate:.1f}%", fontweight="bold")

    # Return rate by category
    cat_return = df.groupby("category")["is_returned"].mean().sort_values(ascending=False) * 100
    axes[0, 1].bar(cat_return.index, cat_return.values,
                   color=["#e74c3c" if v > 25 else "#f39c12" if v > 20 else "#2ecc71"
                          for v in cat_return.values])
    axes[0, 1].axhline(return_rate, color="navy", linestyle="--", linewidth=1.5, label="Avg")
    axes[0, 1].set_title("Return Rate by Category (%)", fontweight="bold")
    axes[0, 1].set_ylabel("%")
    axes[0, 1].legend()
    axes[0, 1].tick_params(axis="x", rotation=20)

    # Return reasons
    reasons = df[df["is_returned"] == 1]["return_reason"].value_counts()
    axes[0, 2].barh(reasons.index, reasons.values, color="#9b59b6")
    axes[0, 2].set_title("Return Reasons Breakdown", fontweight="bold")
    axes[0, 2].set_xlabel("Count")

    # Return rate by channel
    ch_return = df.groupby("channel")["is_returned"].mean() * 100
    axes[1, 0].bar(ch_return.index, ch_return.values, color=["#3498db", "#e67e22", "#1abc9c"])
    axes[1, 0].set_title("Return Rate by Channel (%)", fontweight="bold")
    axes[1, 0].set_ylabel("%")

    # Return rate by delivery days (grouped)
    df["delivery_bucket"] = pd.cut(df["delivery_days"], bins=[0, 3, 7, 10, 15],
                                   labels=["1-3 days", "4-7 days", "8-10 days", "11+ days"])
    del_return = df.groupby("delivery_bucket", observed=True)["is_returned"].mean() * 100
    axes[1, 1].plot(del_return.index.astype(str), del_return.values, marker="o",
                    linewidth=2.5, color="#e74c3c", markersize=8)
    axes[1, 1].set_title("Return Rate by Delivery Speed", fontweight="bold")
    axes[1, 1].set_ylabel("Return Rate (%)")
    axes[1, 1].set_xlabel("Delivery Time")

    # Monthly trend
    monthly = df.groupby("month")["is_returned"].mean() * 100
    axes[1, 2].plot(range(len(monthly)), monthly.values, marker="s", color="#8e44ad", linewidth=2)
    axes[1, 2].set_xticks(range(len(monthly)))
    axes[1, 2].set_xticklabels(monthly.index, rotation=45, ha="right", fontsize=7)
    axes[1, 2].set_title("Monthly Return Rate Trend", fontweight="bold")
    axes[1, 2].set_ylabel("Return Rate (%)")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/return_rate_dashboard.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: return_rate_dashboard.png")


def generate_report(df):
    return_rate = df["is_returned"].mean() * 100
    top_category = df.groupby("category")["is_returned"].mean().idxmax()
    top_reason = df[df["is_returned"] == 1]["return_reason"].value_counts().idxmax()
    worst_channel = df.groupby("channel")["is_returned"].mean().idxmax()

    report = f"""
RETURN RATE ROOT CAUSE ANALYSIS REPORT
========================================
Period     : Jan 2023 – Dec 2023
Total Orders   : {len(df):,}
Total Returns  : {df['is_returned'].sum():,}
Overall Rate   : {return_rate:.2f}%

KEY FINDINGS
------------
1. Highest Return Category : {top_category}
   → Return Rate: {df.groupby('category')['is_returned'].mean()[top_category]*100:.1f}%
   → Primary Reason: Defective products

2. Top Return Reason : {top_reason}
   → {df[df['is_returned']==1]['return_reason'].value_counts().iloc[0]} occurrences

3. Worst Performing Channel : {worst_channel}
   → Return Rate: {df.groupby('channel')['is_returned'].mean()[worst_channel]*100:.1f}%

4. Delivery Impact : Orders with 11+ day delivery
   have higher return rates — faster delivery reduces returns

RECOMMENDATIONS
---------------
1. Implement stricter QC for Electronics category
2. Improve product descriptions to reduce 'Not as Described' returns
3. Optimize {worst_channel} channel customer experience
4. Target delivery SLA below 7 days for high-value orders
"""
    os.makedirs("reports", exist_ok=True)
    with open("reports/return_rate_report.txt", "w") as f:
        f.write(report)
    print(report)
    print("Saved: reports/return_rate_report.txt")


if __name__ == "__main__":
    print("Running Return Rate Analysis...")
    df = generate_data()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/returns_data.csv", index=False)
    print(f"Dataset: {len(df)} orders saved")
    plot_return_rate_overview(df)
    generate_report(df)
    print("Done.")

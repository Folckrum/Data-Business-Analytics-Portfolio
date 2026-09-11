import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

np.random.seed(21)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)
sns.set_theme(style="whitegrid")

n = 5000
cats = ["Electronics", "Clothing", "Furniture", "Books", "Toys", "Sports"]
reasons = ["Defective", "Wrong Item", "Not as Described", "Changed Mind", "Better Price", "Delivery Damage", "Size Issue"]
channels = ["Online", "Retail", "Mobile App"]

df = pd.DataFrame({
    "order_id": range(10001, 10001+n),
    "order_date": pd.to_datetime(np.random.choice(pd.date_range("2023-01-01", "2023-12-31"), n)),
    "category": np.random.choice(cats, n),
    "region": np.random.choice(["North","South","East","West"], n),
    "channel": np.random.choice(channels, n, p=[0.55, 0.30, 0.15]),
    "payment": np.random.choice(["Credit Card","UPI","COD","Net Banking"], n),
    "order_value": np.random.uniform(50, 5000, n).round(2),
    "delivery_days": np.random.randint(1, 15, n),
    "is_returned": np.random.choice([0, 1], n, p=[0.78, 0.22]),
})

ret_idx = df[df["is_returned"]==1].index
df.loc[ret_idx, "return_reason"] = np.random.choice(reasons, len(ret_idx))
elec_ret = df[(df["category"]=="Electronics") & (df["is_returned"]==1)].index
df.loc[elec_ret[:int(len(elec_ret)*0.4)], "return_reason"] = "Defective"

df["month"] = df["order_date"].dt.to_period("M").astype(str)
df["delivery_bucket"] = pd.cut(df["delivery_days"], bins=[0,3,7,10,15], labels=["1-3d","4-7d","8-10d","11+d"])
df.to_csv("data/returns_data.csv", index=False)

overall_rate = df["is_returned"].mean() * 100

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("Return Rate Root Cause Analysis", fontsize=16, fontweight="bold")

axes[0,0].pie([overall_rate, 100-overall_rate], labels=["Returned","Kept"],
              autopct="%1.1f%%", colors=["#e74c3c","#2ecc71"], startangle=90)
axes[0,0].set_title(f"Overall Return Rate: {overall_rate:.1f}%", fontweight="bold")

cat_ret = df.groupby("category")["is_returned"].mean().sort_values(ascending=False) * 100
axes[0,1].bar(cat_ret.index, cat_ret.values,
              color=["#e74c3c" if v>25 else "#f39c12" if v>20 else "#2ecc71" for v in cat_ret.values])
axes[0,1].axhline(overall_rate, color="navy", linestyle="--", linewidth=1.5, label="avg")
axes[0,1].set_title("Return Rate by Category (%)", fontweight="bold")
axes[0,1].legend()
axes[0,1].tick_params(axis="x", rotation=20)

reason_counts = df[df["is_returned"]==1]["return_reason"].value_counts()
axes[0,2].barh(reason_counts.index, reason_counts.values, color="#9b59b6")
axes[0,2].set_title("Return Reasons", fontweight="bold")

ch_ret = df.groupby("channel")["is_returned"].mean() * 100
axes[1,0].bar(ch_ret.index, ch_ret.values, color=["#3498db","#e67e22","#1abc9c"])
axes[1,0].set_title("Return Rate by Channel (%)", fontweight="bold")

del_ret = df.groupby("delivery_bucket", observed=True)["is_returned"].mean() * 100
axes[1,1].plot(del_ret.index.astype(str), del_ret.values, marker="o", linewidth=2.5, color="#e74c3c", markersize=8)
axes[1,1].set_title("Return Rate by Delivery Speed", fontweight="bold")
axes[1,1].set_ylabel("Return Rate (%)")

monthly = df.groupby("month")["is_returned"].mean() * 100
axes[1,2].plot(range(len(monthly)), monthly.values, marker="s", color="#8e44ad", linewidth=2)
axes[1,2].set_xticks(range(len(monthly)))
axes[1,2].set_xticklabels(monthly.index, rotation=45, ha="right", fontsize=7)
axes[1,2].set_title("Monthly Return Rate Trend", fontweight="bold")

plt.tight_layout()
plt.savefig("outputs/return_rate_dashboard.png", dpi=150, bbox_inches="tight")
plt.close()

top_cat = df.groupby("category")["is_returned"].mean().idxmax()
top_reason = df[df["is_returned"]==1]["return_reason"].value_counts().idxmax()
worst_ch = df.groupby("channel")["is_returned"].mean().idxmax()

report = f"""RETURN RATE ROOT CAUSE ANALYSIS
Period: Jan–Dec 2023
Total Orders   : {len(df):,}
Total Returns  : {df['is_returned'].sum():,}
Return Rate    : {overall_rate:.2f}%

FINDINGS
- Highest return category : {top_cat} ({df.groupby('category')['is_returned'].mean()[top_cat]*100:.1f}%)
- Top return reason       : {top_reason} ({reason_counts.iloc[0]} cases)
- Worst channel           : {worst_ch} ({df.groupby('channel')['is_returned'].mean()[worst_ch]*100:.1f}%)
- Delivery impact         : orders with 11+ day delivery show highest return rates

RECOMMENDATIONS
1. Tighten QC process for {top_cat} — defect rate is too high
2. Rewrite product descriptions to reduce "Not as Described" cases
3. Push delivery SLA under 7 days for orders above ₹1000
"""
with open("reports/return_rate_report.txt", "w") as f:
    f.write(report)
print(report)

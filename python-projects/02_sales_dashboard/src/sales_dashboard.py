import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

np.random.seed(99)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

cats = ["Electronics", "Clothing", "Furniture", "Food", "Sports"]
regions = ["North", "South", "East", "West", "Central"]
channels = ["Online", "Retail Store", "Wholesale"]
reps = [f"Rep_{i}" for i in range(1, 16)]
n = 2000

df = pd.DataFrame({
    "order_id": range(1001, 1001+n),
    "date": pd.date_range("2023-01-01", "2023-12-31", periods=n),
    "category": np.random.choice(cats, n),
    "region": np.random.choice(regions, n),
    "channel": np.random.choice(channels, n, p=[0.50, 0.35, 0.15]),
    "sales_rep": np.random.choice(reps, n),
    "units": np.random.randint(1, 50, n),
    "unit_price": np.random.uniform(10, 500, n).round(2),
    "discount_pct": np.random.choice([0, 5, 10, 15, 20], n, p=[0.4, 0.2, 0.2, 0.1, 0.1]),
    "cost_per_unit": np.random.uniform(5, 300, n).round(2),
})

df["revenue"] = (df["units"] * df["unit_price"] * (1 - df["discount_pct"]/100)).round(2)
df["cost"] = (df["units"] * df["cost_per_unit"]).round(2)
df["profit"] = (df["revenue"] - df["cost"]).round(2)
df["margin"] = (df["profit"] / df["revenue"] * 100).round(2)
df["month"] = df["date"].dt.to_period("M").astype(str)
df["quarter"] = "Q" + df["date"].dt.quarter.astype(str)
df.to_csv("data/sales_data.csv", index=False)

fig = plt.figure(figsize=(20, 14))
fig.suptitle("Sales Performance Dashboard — FY 2023", fontsize=18, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

ax_kpi = fig.add_subplot(gs[0, :])
ax_kpi.axis("off")
kpis = [
    ("Total Revenue", f"₹{df['revenue'].sum():,.0f}"),
    ("Total Profit", f"₹{df['profit'].sum():,.0f}"),
    ("Units Sold", f"{df['units'].sum():,}"),
    ("Avg Margin", f"{df['margin'].mean():.1f}%"),
    ("Top Region", df.groupby('region')['revenue'].sum().idxmax()),
]
for i, (label, val) in enumerate(kpis):
    x = 0.1 + i * 0.19
    ax_kpi.text(x, 0.65, val, ha="center", fontsize=16, fontweight="bold", color="#2c3e50", transform=ax_kpi.transAxes)
    ax_kpi.text(x, 0.25, label, ha="center", fontsize=10, color="#7f8c8d", transform=ax_kpi.transAxes)

ax1 = fig.add_subplot(gs[1, :2])
monthly = df.groupby("month")["revenue"].sum().reset_index()
ax1.plot(monthly["month"], monthly["revenue"], marker="o", linewidth=2.5, color="#3498db", markersize=6)
ax1.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.15, color="#3498db")
ax1.set_xticks(range(len(monthly)))
ax1.set_xticklabels(monthly["month"], rotation=45, ha="right", fontsize=8)
ax1.set_title("Monthly Revenue", fontweight="bold")
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

ax2 = fig.add_subplot(gs[1, 2])
cat_rev = df.groupby("category")["revenue"].sum().sort_values()
ax2.barh(cat_rev.index, cat_rev.values, color=["#e74c3c","#e67e22","#f1c40f","#2ecc71","#3498db"])
ax2.set_title("Revenue by Category", fontweight="bold")
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

ax3 = fig.add_subplot(gs[2, 0])
rd = df.groupby("region").agg(revenue=("revenue","sum"), profit=("profit","sum")).reset_index()
x = range(len(rd))
ax3.bar([i-0.2 for i in x], rd["revenue"], width=0.4, label="Revenue", color="#3498db")
ax3.bar([i+0.2 for i in x], rd["profit"], width=0.4, label="Profit", color="#2ecc71")
ax3.set_xticks(list(x))
ax3.set_xticklabels(rd["region"], rotation=15)
ax3.set_title("Revenue vs Profit by Region", fontweight="bold")
ax3.legend(fontsize=8)
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

ax4 = fig.add_subplot(gs[2, 1])
ch = df.groupby("channel")["revenue"].sum()
ax4.pie(ch.values, labels=ch.index, autopct="%1.1f%%", colors=["#3498db","#e74c3c","#2ecc71"], startangle=90)
ax4.set_title("Revenue by Channel", fontweight="bold")

ax5 = fig.add_subplot(gs[2, 2])
qd = df.groupby("quarter").agg(revenue=("revenue","sum"), profit=("profit","sum")).reset_index()
ax5.bar(qd["quarter"], qd["revenue"], color="#9b59b6", label="Revenue")
ax5.bar(qd["quarter"], qd["profit"], color="#e67e22", label="Profit")
ax5.set_title("Quarterly Performance", fontweight="bold")
ax5.legend(fontsize=8)
ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

plt.savefig("outputs/sales_dashboard.png", dpi=150, bbox_inches="tight")
plt.close()

rep_stats = df.groupby("sales_rep").agg(total=("revenue","sum"), margin=("margin","mean")).sort_values("total", ascending=False).head(10).reset_index()
plt.figure(figsize=(12, 6))
bars = plt.bar(rep_stats["sales_rep"], rep_stats["total"], color=plt.cm.RdYlGn(np.linspace(0.3, 0.9, 10)))
plt.title("Top 10 Sales Reps by Revenue", fontsize=14, fontweight="bold")
plt.ylabel("Revenue (₹)")
plt.xticks(rotation=30, ha="right")
plt.yaxis = plt.gca().yaxis
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))
for bar, m in zip(bars, rep_stats["margin"]):
    plt.text(bar.get_x()+bar.get_width()/2, bar.get_height()+200, f"{m:.1f}%", ha="center", fontsize=8)
plt.tight_layout()
plt.savefig("outputs/top_reps.png", dpi=150)
plt.close()

print(f"revenue: ₹{df['revenue'].sum():,.0f}")
print(f"profit: ₹{df['profit'].sum():,.0f}")
print(f"top category: {df.groupby('category')['revenue'].sum().idxmax()}")

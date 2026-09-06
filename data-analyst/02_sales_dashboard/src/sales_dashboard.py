import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os

np.random.seed(99)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_sales_data(n=2000):
    categories = ["Electronics", "Clothing", "Furniture", "Food", "Sports"]
    regions = ["North", "South", "East", "West", "Central"]
    channels = ["Online", "Retail Store", "Wholesale"]
    reps = [f"Rep_{i}" for i in range(1, 16)]

    dates = pd.date_range(start="2023-01-01", end="2023-12-31", periods=n)

    df = pd.DataFrame({
        "order_id": range(1001, 1001 + n),
        "date": dates,
        "category": np.random.choice(categories, n),
        "region": np.random.choice(regions, n),
        "channel": np.random.choice(channels, n, p=[0.50, 0.35, 0.15]),
        "sales_rep": np.random.choice(reps, n),
        "units_sold": np.random.randint(1, 50, n),
        "unit_price": np.random.uniform(10, 500, n).round(2),
        "discount_pct": np.random.choice([0, 5, 10, 15, 20], n, p=[0.4, 0.2, 0.2, 0.1, 0.1]),
        "cost_per_unit": np.random.uniform(5, 300, n).round(2),
    })

    df["revenue"] = (df["units_sold"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)
    df["cost"] = (df["units_sold"] * df["cost_per_unit"]).round(2)
    df["profit"] = (df["revenue"] - df["cost"]).round(2)
    df["profit_margin"] = (df["profit"] / df["revenue"] * 100).round(2)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["quarter"] = df["date"].dt.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    df["week"] = df["date"].dt.isocalendar().week
    return df


def plot_executive_dashboard(df):
    fig = plt.figure(figsize=(20, 14))
    fig.suptitle("Sales Performance Dashboard — FY 2023", fontsize=18, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    # KPI Summary Row
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.axis("off")
    total_rev = df["revenue"].sum()
    total_profit = df["profit"].sum()
    total_units = df["units_sold"].sum()
    avg_margin = df["profit_margin"].mean()
    top_region = df.groupby("region")["revenue"].sum().idxmax()

    kpis = [
        ("Total Revenue", f"₹{total_rev:,.0f}"),
        ("Total Profit", f"₹{total_profit:,.0f}"),
        ("Units Sold", f"{total_units:,}"),
        ("Avg Profit Margin", f"{avg_margin:.1f}%"),
        ("Top Region", top_region),
    ]
    for i, (label, val) in enumerate(kpis):
        x = 0.1 + i * 0.19
        ax_kpi.text(x, 0.65, val, ha="center", fontsize=16, fontweight="bold", color="#2c3e50",
                    transform=ax_kpi.transAxes)
        ax_kpi.text(x, 0.25, label, ha="center", fontsize=10, color="#7f8c8d",
                    transform=ax_kpi.transAxes)
        if i < 4:
            ax_kpi.axvline(x + 0.095, 0.1, 0.9, color="#bdc3c7", linewidth=1,
                           transform=ax_kpi.transAxes)

    # Monthly Revenue Trend
    ax1 = fig.add_subplot(gs[1, :2])
    monthly = df.groupby("month")["revenue"].sum().reset_index()
    ax1.plot(monthly["month"], monthly["revenue"], marker="o", linewidth=2.5,
             color="#3498db", markersize=6)
    ax1.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.15, color="#3498db")
    ax1.set_xticks(range(len(monthly)))
    ax1.set_xticklabels(monthly["month"], rotation=45, ha="right", fontsize=8)
    ax1.set_title("Monthly Revenue Trend", fontweight="bold")
    ax1.set_ylabel("Revenue (₹)")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

    # Revenue by Category
    ax2 = fig.add_subplot(gs[1, 2])
    cat_rev = df.groupby("category")["revenue"].sum().sort_values()
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
    ax2.barh(cat_rev.index, cat_rev.values, color=colors)
    ax2.set_title("Revenue by Category", fontweight="bold")
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

    # Regional Performance
    ax3 = fig.add_subplot(gs[2, 0])
    region_data = df.groupby("region").agg(revenue=("revenue", "sum"),
                                           profit=("profit", "sum")).reset_index()
    x = range(len(region_data))
    ax3.bar([i - 0.2 for i in x], region_data["revenue"], width=0.4, label="Revenue", color="#3498db")
    ax3.bar([i + 0.2 for i in x], region_data["profit"], width=0.4, label="Profit", color="#2ecc71")
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(region_data["region"], rotation=15)
    ax3.set_title("Revenue vs Profit by Region", fontweight="bold")
    ax3.legend(fontsize=8)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

    # Channel Split
    ax4 = fig.add_subplot(gs[2, 1])
    channel_rev = df.groupby("channel")["revenue"].sum()
    ax4.pie(channel_rev.values, labels=channel_rev.index, autopct="%1.1f%%",
            colors=["#3498db", "#e74c3c", "#2ecc71"], startangle=90)
    ax4.set_title("Revenue by Channel", fontweight="bold")

    # Quarterly Comparison
    ax5 = fig.add_subplot(gs[2, 2])
    q_data = df.groupby("quarter").agg(revenue=("revenue", "sum"),
                                       profit=("profit", "sum")).reset_index()
    ax5.bar(q_data["quarter"], q_data["revenue"], color="#9b59b6", label="Revenue")
    ax5.bar(q_data["quarter"], q_data["profit"], color="#e67e22", label="Profit")
    ax5.set_title("Quarterly Performance", fontweight="bold")
    ax5.legend(fontsize=8)
    ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

    plt.savefig(f"{OUTPUT_DIR}/sales_dashboard.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: sales_dashboard.png")


def top_sales_reps(df):
    rep_stats = df.groupby("sales_rep").agg(
        total_revenue=("revenue", "sum"),
        total_profit=("profit", "sum"),
        orders=("order_id", "count"),
        avg_margin=("profit_margin", "mean")
    ).sort_values("total_revenue", ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(rep_stats["sales_rep"], rep_stats["total_revenue"],
                  color=plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(rep_stats))))
    ax.set_title("Top 10 Sales Representatives by Revenue", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Revenue (₹)")
    ax.set_xlabel("Sales Rep")
    plt.xticks(rotation=30, ha="right")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}K"))

    for bar, margin in zip(bars, rep_stats["avg_margin"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
                f"{margin:.1f}%", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/top_sales_reps.png", dpi=150)
    plt.close()
    print("Saved: top_sales_reps.png")


def print_summary(df):
    print("\n" + "=" * 55)
    print("        SALES DASHBOARD — SUMMARY REPORT")
    print("=" * 55)
    print(f"Total Revenue     : ₹{df['revenue'].sum():,.2f}")
    print(f"Total Profit      : ₹{df['profit'].sum():,.2f}")
    print(f"Total Orders      : {len(df):,}")
    print(f"Units Sold        : {df['units_sold'].sum():,}")
    print(f"Avg Profit Margin : {df['profit_margin'].mean():.2f}%")
    print(f"Top Category      : {df.groupby('category')['revenue'].sum().idxmax()}")
    print(f"Top Region        : {df.groupby('region')['revenue'].sum().idxmax()}")
    print(f"Top Channel       : {df.groupby('channel')['revenue'].sum().idxmax()}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    print("Building Sales Dashboard...")
    df = generate_sales_data()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/sales_data.csv", index=False)
    print(f"Dataset: {len(df)} records saved")
    plot_executive_dashboard(df)
    top_sales_reps(df)
    print_summary(df)
    print("Done.")

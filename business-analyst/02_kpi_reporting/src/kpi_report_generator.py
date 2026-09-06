import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from datetime import datetime

np.random.seed(55)
OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_kpi_data():
    months = pd.date_range("2023-01-01", "2023-12-31", freq="MS")
    n = len(months)

    df = pd.DataFrame({
        "month": months,
        "revenue": np.random.uniform(800000, 2000000, n).round(0),
        "new_customers": np.random.randint(200, 1000, n),
        "active_customers": np.random.randint(2000, 8000, n),
        "churn_rate": np.random.uniform(2, 8, n).round(2),
        "avg_order_value": np.random.uniform(150, 400, n).round(2),
        "cac": np.random.uniform(40, 120, n).round(2),
        "cltv": np.random.uniform(500, 2000, n).round(2),
        "nps_score": np.random.randint(30, 80, n),
        "support_tickets": np.random.randint(100, 600, n),
        "resolution_time_hrs": np.random.uniform(1, 24, n).round(1),
    })

    df["revenue_growth_pct"] = df["revenue"].pct_change() * 100
    df["customer_growth_pct"] = df["new_customers"].pct_change() * 100
    df["cltv_cac_ratio"] = (df["cltv"] / df["cac"]).round(2)
    df["month_label"] = df["month"].dt.strftime("%b %Y")
    return df


def compute_kpis(df):
    current = df.iloc[-1]
    previous = df.iloc[-2]

    def delta(curr, prev):
        return ((curr - prev) / prev * 100) if prev != 0 else 0

    return {
        "Revenue": {
            "value": f"₹{current['revenue']:,.0f}",
            "change": delta(current["revenue"], previous["revenue"]),
            "unit": "%"
        },
        "New Customers": {
            "value": f"{current['new_customers']:,}",
            "change": delta(current["new_customers"], previous["new_customers"]),
            "unit": "%"
        },
        "Avg Order Value": {
            "value": f"₹{current['avg_order_value']:.2f}",
            "change": delta(current["avg_order_value"], previous["avg_order_value"]),
            "unit": "%"
        },
        "Churn Rate": {
            "value": f"{current['churn_rate']:.2f}%",
            "change": delta(current["churn_rate"], previous["churn_rate"]),
            "unit": "%",
            "inverse": True
        },
        "NPS Score": {
            "value": str(int(current["nps_score"])),
            "change": delta(current["nps_score"], previous["nps_score"]),
            "unit": "pts"
        },
        "CLTV/CAC Ratio": {
            "value": f"{current['cltv_cac_ratio']:.1f}x",
            "change": delta(current["cltv_cac_ratio"], previous["cltv_cac_ratio"]),
            "unit": "%"
        },
    }


def build_kpi_dashboard(df, kpis):
    fig = plt.figure(figsize=(20, 16))
    fig.patch.set_facecolor("#f8f9fa")
    fig.suptitle(
        f"Business KPI Dashboard — {df['month_label'].iloc[-1]}",
        fontsize=18, fontweight="bold", y=0.98, color="#2c3e50"
    )
    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.5, wspace=0.35)

    # KPI Cards
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.set_facecolor("#ecf0f1")
    ax_kpi.axis("off")

    for i, (name, kpi) in enumerate(kpis.items()):
        x = 0.08 + i * 0.155
        change = kpi["change"]
        inverse = kpi.get("inverse", False)
        color = "#27ae60" if (change > 0) != inverse else "#e74c3c"
        arrow = "▲" if change > 0 else "▼"

        ax_kpi.text(x, 0.75, kpi["value"], ha="center", fontsize=14, fontweight="bold",
                    color="#2c3e50", transform=ax_kpi.transAxes)
        ax_kpi.text(x, 0.4, f"{arrow} {abs(change):.1f}%", ha="center", fontsize=10,
                    color=color, transform=ax_kpi.transAxes)
        ax_kpi.text(x, 0.08, name, ha="center", fontsize=9, color="#7f8c8d",
                    transform=ax_kpi.transAxes)

    # Revenue Trend
    ax1 = fig.add_subplot(gs[1, :2])
    ax1.set_facecolor("white")
    ax1.plot(df["month_label"], df["revenue"] / 1e6, marker="o", linewidth=2.5,
             color="#3498db", markersize=5)
    ax1.fill_between(range(len(df)), df["revenue"] / 1e6, alpha=0.1, color="#3498db")
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(df["month_label"], rotation=45, ha="right", fontsize=8)
    ax1.set_title("Monthly Revenue (₹ Millions)", fontweight="bold")
    ax1.set_ylabel("Revenue (₹M)")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:.1f}M"))

    # Customer Growth
    ax2 = fig.add_subplot(gs[1, 2])
    ax2.set_facecolor("white")
    ax2.bar(range(len(df)), df["new_customers"], color="#2ecc71", alpha=0.85)
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(df["month_label"], rotation=45, ha="right", fontsize=7)
    ax2.set_title("New Customers per Month", fontweight="bold")
    ax2.set_ylabel("Customers")

    # Churn Rate
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.set_facecolor("white")
    colors = ["#e74c3c" if v > 5 else "#f39c12" if v > 3 else "#2ecc71" for v in df["churn_rate"]]
    ax3.bar(range(len(df)), df["churn_rate"], color=colors)
    ax3.axhline(5, color="red", linestyle="--", linewidth=1, label="5% threshold")
    ax3.set_xticks(range(len(df)))
    ax3.set_xticklabels(df["month_label"], rotation=45, ha="right", fontsize=7)
    ax3.set_title("Monthly Churn Rate (%)", fontweight="bold")
    ax3.set_ylabel("Churn %")
    ax3.legend(fontsize=8)

    # NPS Score Trend
    ax4 = fig.add_subplot(gs[2, 1])
    ax4.set_facecolor("white")
    ax4.plot(df["month_label"], df["nps_score"], marker="D", linewidth=2,
             color="#9b59b6", markersize=6)
    ax4.axhline(50, color="green", linestyle="--", linewidth=1, label="Good (50)")
    ax4.set_xticks(range(len(df)))
    ax4.set_xticklabels(df["month_label"], rotation=45, ha="right", fontsize=7)
    ax4.set_title("NPS Score Trend", fontweight="bold")
    ax4.set_ylabel("NPS")
    ax4.legend(fontsize=8)

    # CLTV/CAC Ratio
    ax5 = fig.add_subplot(gs[2, 2])
    ax5.set_facecolor("white")
    bar_colors = ["#27ae60" if v >= 3 else "#e67e22" if v >= 2 else "#e74c3c"
                  for v in df["cltv_cac_ratio"]]
    ax5.bar(range(len(df)), df["cltv_cac_ratio"], color=bar_colors)
    ax5.axhline(3, color="green", linestyle="--", linewidth=1, label="Healthy (3x)")
    ax5.set_xticks(range(len(df)))
    ax5.set_xticklabels(df["month_label"], rotation=45, ha="right", fontsize=7)
    ax5.set_title("CLTV / CAC Ratio", fontweight="bold")
    ax5.set_ylabel("Ratio")
    ax5.legend(fontsize=8)

    # Avg Order Value
    ax6 = fig.add_subplot(gs[3, :])
    ax6.set_facecolor("white")
    ax6.plot(df["month_label"], df["avg_order_value"], marker="^", linewidth=2.5,
             color="#e67e22", markersize=7, label="Avg Order Value")
    ax6_twin = ax6.twinx()
    ax6_twin.bar(range(len(df)), df["support_tickets"], alpha=0.3,
                 color="#e74c3c", label="Support Tickets")
    ax6.set_xticks(range(len(df)))
    ax6.set_xticklabels(df["month_label"], rotation=30, ha="right", fontsize=8)
    ax6.set_title("Avg Order Value vs Support Tickets", fontweight="bold")
    ax6.set_ylabel("Avg Order Value (₹)", color="#e67e22")
    ax6_twin.set_ylabel("Support Tickets", color="#e74c3c")
    ax6.legend(loc="upper left", fontsize=9)
    ax6_twin.legend(loc="upper right", fontsize=9)

    plt.savefig(f"{OUTPUT_DIR}/kpi_dashboard.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("Saved: reports/kpi_dashboard.png")


if __name__ == "__main__":
    print("Generating KPI Report...")
    df = generate_kpi_data()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/kpi_data.csv", index=False)
    kpis = compute_kpis(df)
    build_kpi_dashboard(df, kpis)
    print("\nKPI Summary (Latest Month):")
    for name, data in kpis.items():
        direction = "▲" if data["change"] > 0 else "▼"
        print(f"  {name:20s}: {data['value']:>12}  {direction} {abs(data['change']):.1f}%")
    print("\nDone.")

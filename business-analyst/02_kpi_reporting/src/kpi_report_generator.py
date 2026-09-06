import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

np.random.seed(55)
os.makedirs("reports", exist_ok=True)
os.makedirs("data", exist_ok=True)

months = pd.date_range("2023-01-01", "2023-12-31", freq="MS")
n = len(months)

df = pd.DataFrame({
    "month": months,
    "revenue": np.random.uniform(800000, 2000000, n).round(0),
    "new_customers": np.random.randint(200, 1000, n),
    "active_customers": np.random.randint(2000, 8000, n),
    "churn_rate": np.random.uniform(2, 8, n).round(2),
    "aov": np.random.uniform(150, 400, n).round(2),
    "cac": np.random.uniform(40, 120, n).round(2),
    "cltv": np.random.uniform(500, 2000, n).round(2),
    "nps": np.random.randint(30, 80, n),
    "tickets": np.random.randint(100, 600, n),
})
df["cltv_cac"] = (df["cltv"] / df["cac"]).round(2)
df["label"] = df["month"].dt.strftime("%b %Y")
df.to_csv("data/kpi_data.csv", index=False)

curr, prev = df.iloc[-1], df.iloc[-2]
def chg(c, p): return (c - p) / p * 100 if p else 0

kpis = {
    "Revenue":        (f"₹{curr['revenue']:,.0f}", chg(curr['revenue'], prev['revenue']), False),
    "New Customers":  (f"{curr['new_customers']:,}", chg(curr['new_customers'], prev['new_customers']), False),
    "Avg Order Value":(f"₹{curr['aov']:.2f}", chg(curr['aov'], prev['aov']), False),
    "Churn Rate":     (f"{curr['churn_rate']:.2f}%", chg(curr['churn_rate'], prev['churn_rate']), True),
    "NPS Score":      (f"{int(curr['nps'])}", chg(curr['nps'], prev['nps']), False),
    "CLTV/CAC":       (f"{curr['cltv_cac']:.1f}x", chg(curr['cltv_cac'], prev['cltv_cac']), False),
}

fig = plt.figure(figsize=(20, 16))
fig.patch.set_facecolor("#f8f9fa")
fig.suptitle(f"Business KPI Dashboard — {curr['label']}", fontsize=18, fontweight="bold", y=0.98, color="#2c3e50")
gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.5, wspace=0.35)

ax_k = fig.add_subplot(gs[0, :])
ax_k.set_facecolor("#ecf0f1")
ax_k.axis("off")
for i, (name, (val, change, inverse)) in enumerate(kpis.items()):
    x = 0.08 + i * 0.155
    color = "#27ae60" if (change > 0) != inverse else "#e74c3c"
    arrow = "▲" if change > 0 else "▼"
    ax_k.text(x, 0.75, val, ha="center", fontsize=14, fontweight="bold", color="#2c3e50", transform=ax_k.transAxes)
    ax_k.text(x, 0.40, f"{arrow} {abs(change):.1f}%", ha="center", fontsize=10, color=color, transform=ax_k.transAxes)
    ax_k.text(x, 0.08, name, ha="center", fontsize=9, color="#7f8c8d", transform=ax_k.transAxes)

ax1 = fig.add_subplot(gs[1, :2])
ax1.plot(df["label"], df["revenue"]/1e6, marker="o", linewidth=2.5, color="#3498db", markersize=5)
ax1.fill_between(range(n), df["revenue"]/1e6, alpha=0.1, color="#3498db")
ax1.set_xticks(range(n))
ax1.set_xticklabels(df["label"], rotation=45, ha="right", fontsize=8)
ax1.set_title("Monthly Revenue (₹M)", fontweight="bold")
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:.1f}M"))

ax2 = fig.add_subplot(gs[1, 2])
ax2.bar(range(n), df["new_customers"], color="#2ecc71", alpha=0.85)
ax2.set_xticks(range(n))
ax2.set_xticklabels(df["label"], rotation=45, ha="right", fontsize=7)
ax2.set_title("New Customers / Month", fontweight="bold")

ax3 = fig.add_subplot(gs[2, 0])
c_colors = ["#e74c3c" if v>5 else "#f39c12" if v>3 else "#2ecc71" for v in df["churn_rate"]]
ax3.bar(range(n), df["churn_rate"], color=c_colors)
ax3.axhline(5, color="red", linestyle="--", linewidth=1, label="5% threshold")
ax3.set_xticks(range(n))
ax3.set_xticklabels(df["label"], rotation=45, ha="right", fontsize=7)
ax3.set_title("Churn Rate (%)", fontweight="bold")
ax3.legend(fontsize=8)

ax4 = fig.add_subplot(gs[2, 1])
ax4.plot(df["label"], df["nps"], marker="D", linewidth=2, color="#9b59b6", markersize=6)
ax4.axhline(50, color="green", linestyle="--", linewidth=1, label="Good (50)")
ax4.set_xticks(range(n))
ax4.set_xticklabels(df["label"], rotation=45, ha="right", fontsize=7)
ax4.set_title("NPS Score", fontweight="bold")
ax4.legend(fontsize=8)

ax5 = fig.add_subplot(gs[2, 2])
ratio_colors = ["#27ae60" if v>=3 else "#e67e22" if v>=2 else "#e74c3c" for v in df["cltv_cac"]]
ax5.bar(range(n), df["cltv_cac"], color=ratio_colors)
ax5.axhline(3, color="green", linestyle="--", linewidth=1, label="Healthy (3x)")
ax5.set_xticks(range(n))
ax5.set_xticklabels(df["label"], rotation=45, ha="right", fontsize=7)
ax5.set_title("CLTV / CAC Ratio", fontweight="bold")
ax5.legend(fontsize=8)

ax6 = fig.add_subplot(gs[3, :])
ax6.plot(df["label"], df["aov"], marker="^", linewidth=2.5, color="#e67e22", markersize=7, label="Avg Order Value")
ax6b = ax6.twinx()
ax6b.bar(range(n), df["tickets"], alpha=0.3, color="#e74c3c", label="Support Tickets")
ax6.set_xticks(range(n))
ax6.set_xticklabels(df["label"], rotation=30, ha="right", fontsize=8)
ax6.set_title("AOV vs Support Tickets", fontweight="bold")
ax6.set_ylabel("AOV (₹)", color="#e67e22")
ax6b.set_ylabel("Tickets", color="#e74c3c")
ax6.legend(loc="upper left", fontsize=9)
ax6b.legend(loc="upper right", fontsize=9)

plt.savefig("reports/kpi_dashboard.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()

print("KPIs (latest month):")
for name, (val, change, _) in kpis.items():
    print(f"  {name:<20}: {val:>12}  {'▲' if change>0 else '▼'} {abs(change):.1f}%")

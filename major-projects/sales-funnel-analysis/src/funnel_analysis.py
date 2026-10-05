import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

np.random.seed(42)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ── Generate Data ─────────────────────────────────────────────
n = 50000
channels = ["Organic", "Paid Ads", "Email", "Social Media", "Direct"]
devices = ["Mobile", "Desktop", "Tablet"]
categories = ["Electronics", "Clothing", "Furniture", "Sports", "Books"]

df = pd.DataFrame({
    "user_id": [f"U{i:06d}" for i in range(n)],
    "channel": np.random.choice(channels, n, p=[0.30, 0.25, 0.20, 0.15, 0.10]),
    "device": np.random.choice(devices, n, p=[0.55, 0.35, 0.10]),
    "category": np.random.choice(categories, n),
    "date": pd.to_datetime(np.random.choice(pd.date_range("2024-01-01", "2024-12-31"), n)),
    "visit": 1,
})

# funnel drop-off probabilities per channel
channel_conv = {
    "Organic":      [1.0, 0.62, 0.41, 0.28, 0.18],
    "Paid Ads":     [1.0, 0.55, 0.33, 0.20, 0.11],
    "Email":        [1.0, 0.70, 0.52, 0.38, 0.26],
    "Social Media": [1.0, 0.48, 0.27, 0.14, 0.07],
    "Direct":       [1.0, 0.65, 0.45, 0.32, 0.22],
}

stages = ["product_view", "add_to_cart", "checkout", "purchase"]
for i, stage in enumerate(stages):
    df[stage] = df.apply(
        lambda r: int(np.random.random() < channel_conv[r["channel"]][i + 1]), axis=1
    )
    # enforce funnel logic — can't reach next stage without previous
    if i > 0:
        df[stage] = df[stage] & df[stages[i - 1]]

df.to_csv("data/funnel_data.csv", index=False)
print(f"dataset: {len(df):,} users")

# ── Funnel Metrics ────────────────────────────────────────────
all_stages = ["visit", "product_view", "add_to_cart", "checkout", "purchase"]
stage_labels = ["Visit", "Product View", "Add to Cart", "Checkout", "Purchase"]

totals = [df[s].sum() for s in all_stages]
pct_of_top = [t / totals[0] * 100 for t in totals]
step_conv = [100.0] + [totals[i] / totals[i-1] * 100 for i in range(1, len(totals))]
drop_off = [0] + [totals[i-1] - totals[i] for i in range(1, len(totals))]

funnel_df = pd.DataFrame({
    "stage": stage_labels,
    "users": totals,
    "pct_of_visits": [round(p, 1) for p in pct_of_top],
    "step_conversion": [round(s, 1) for s in step_conv],
    "drop_off_users": drop_off,
})
funnel_df.to_csv("outputs/funnel_summary.csv", index=False)
print("\nFunnel Summary:")
print(funnel_df.to_string(index=False))

# ── Channel Breakdown ─────────────────────────────────────────
ch = df.groupby("channel").agg(
    visits=("visit", "sum"),
    purchases=("purchase", "sum"),
    cart_adds=("add_to_cart", "sum"),
).reset_index()
ch["overall_conv_pct"] = (ch["purchases"] / ch["visits"] * 100).round(2)
ch["cart_conv_pct"] = (ch["purchases"] / ch["cart_adds"].replace(0, np.nan) * 100).round(2)
ch = ch.sort_values("overall_conv_pct", ascending=False)
ch.to_csv("outputs/channel_breakdown.csv", index=False)

# ── Device Breakdown ──────────────────────────────────────────
dv = df.groupby("device").agg(
    visits=("visit", "sum"),
    purchases=("purchase", "sum"),
    cart_adds=("add_to_cart", "sum"),
    checkouts=("checkout", "sum"),
).reset_index()
dv["overall_conv_pct"] = (dv["purchases"] / dv["visits"] * 100).round(2)
dv["checkout_to_purchase"] = (dv["purchases"] / dv["checkouts"].replace(0, np.nan) * 100).round(2)
dv.to_csv("outputs/device_breakdown.csv", index=False)

# ── Monthly Trend ─────────────────────────────────────────────
df["month"] = df["date"].dt.to_period("M").astype(str)
monthly = df.groupby("month").agg(
    visits=("visit", "sum"),
    purchases=("purchase", "sum"),
).reset_index()
monthly["conv_pct"] = (monthly["purchases"] / monthly["visits"] * 100).round(2)
monthly.to_csv("outputs/monthly_trend.csv", index=False)

# ── Plots ─────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle("E-Commerce Sales Funnel Analysis", fontsize=18, fontweight="bold", y=0.98)
fig.patch.set_facecolor("#f8f9fa")

colors = ["#3498db", "#2ecc71", "#f39c12", "#e67e22", "#e74c3c"]

# 1. Funnel bar
ax = axes[0, 0]
bars = ax.barh(stage_labels[::-1], totals[::-1], color=colors[::-1], height=0.55)
ax.set_title("Funnel — User Volume per Stage", fontweight="bold")
ax.set_xlabel("Users")
for bar, val, pct in zip(bars, totals[::-1], pct_of_top[::-1]):
    ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
            f"{val:,} ({pct:.1f}%)", va="center", fontsize=9, fontweight="bold")
ax.set_xlim(0, max(totals) * 1.25)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x/1000)}K"))

# 2. Step conversion rates
ax2 = axes[0, 1]
step_labels = ["Visit→View", "View→Cart", "Cart→Checkout", "Checkout→Purchase"]
step_vals = step_conv[1:]
bar_colors = ["#27ae60" if v >= 50 else "#e67e22" if v >= 30 else "#e74c3c" for v in step_vals]
bars2 = ax2.bar(step_labels, step_vals, color=bar_colors, width=0.5)
ax2.set_title("Step-by-Step Conversion Rate (%)", fontweight="bold")
ax2.set_ylabel("%")
ax2.set_ylim(0, 100)
for bar, val in zip(bars2, step_vals):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f"{val:.1f}%", ha="center", fontsize=11, fontweight="bold")
ax2.tick_params(axis="x", rotation=15)

# 3. Channel conversion
ax3 = axes[0, 2]
ax3.bar(ch["channel"], ch["overall_conv_pct"],
        color=["#3498db","#2ecc71","#9b59b6","#e67e22","#e74c3c"])
ax3.set_title("Overall Conversion Rate by Channel (%)", fontweight="bold")
ax3.set_ylabel("%")
ax3.tick_params(axis="x", rotation=15)
for i, (_, row) in enumerate(ch.iterrows()):
    ax3.text(i, row["overall_conv_pct"] + 0.1, f"{row['overall_conv_pct']:.1f}%",
             ha="center", fontsize=10, fontweight="bold")

# 4. Device heatmap-style
ax4 = axes[1, 0]
device_stages = ["visits", "cart_adds", "checkouts", "purchases"]
device_stage_labels = ["Visits", "Cart Adds", "Checkouts", "Purchases"]
x = np.arange(len(device_stages))
width = 0.25
dev_colors = ["#3498db", "#2ecc71", "#e67e22"]
for i, (_, row) in enumerate(dv.iterrows()):
    vals = [row[s] for s in device_stages]
    ax4.bar(x + i*width, vals, width=width, label=row["device"], color=dev_colors[i], alpha=0.85)
ax4.set_title("Funnel by Device", fontweight="bold")
ax4.set_xticks(x + width)
ax4.set_xticklabels(device_stage_labels)
ax4.legend(fontsize=9)
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x/1000)}K"))

# 5. Monthly conversion trend
ax5 = axes[1, 1]
ax5.plot(range(len(monthly)), monthly["conv_pct"], marker="o", linewidth=2.5,
         color="#9b59b6", markersize=7)
ax5.fill_between(range(len(monthly)), monthly["conv_pct"], alpha=0.15, color="#9b59b6")
ax5.set_title("Monthly Overall Conversion Rate (%)", fontweight="bold")
ax5.set_ylabel("%")
ax5.set_xticks(range(len(monthly)))
ax5.set_xticklabels(monthly["month"], rotation=45, ha="right", fontsize=8)
ax5.axhline(monthly["conv_pct"].mean(), color="red", linestyle="--", linewidth=1,
            label=f"avg {monthly['conv_pct'].mean():.1f}%")
ax5.legend(fontsize=9)

# 6. Drop-off waterfall
ax6 = axes[1, 2]
drop_vals = drop_off[1:]
drop_labels = ["View→Cart", "Cart→Checkout", "Checkout→Purchase", "Lost at Purchase"]
# actually show users lost at each transition
lost = [totals[i] - totals[i+1] for i in range(len(totals)-1)]
lost_labels = [f"{stage_labels[i]}→{stage_labels[i+1]}" for i in range(len(stage_labels)-1)]
bars6 = ax6.bar(lost_labels, lost, color=["#e74c3c","#e67e22","#f39c12","#c0392b"], width=0.5)
ax6.set_title("Users Lost at Each Stage", fontweight="bold")
ax6.set_ylabel("Users Lost")
ax6.tick_params(axis="x", rotation=20)
for bar, val in zip(bars6, lost):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
             f"{val:,}", ha="center", fontsize=9, fontweight="bold")
ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x/1000)}K"))

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("outputs/funnel_dashboard.png", dpi=150, bbox_inches="tight")
plt.close()
print("\noutputs saved.")

# ── Print Summary ─────────────────────────────────────────────
print("\n" + "="*50)
print(f"  Total Visitors      : {totals[0]:,}")
print(f"  Total Purchases     : {totals[4]:,}")
print(f"  Overall Conv Rate   : {pct_of_top[4]:.2f}%")
print(f"  Biggest Drop-off    : {stage_labels[lost.index(max(lost))]} → {stage_labels[lost.index(max(lost))+1]} ({max(lost):,} users)")
print(f"  Best Channel        : {ch.iloc[0]['channel']} ({ch.iloc[0]['overall_conv_pct']}% conv)")
print(f"  Best Device         : {dv.sort_values('overall_conv_pct', ascending=False).iloc[0]['device']}")
print("="*50)

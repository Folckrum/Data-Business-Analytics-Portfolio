import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.preprocessing import MinMaxScaler
import os
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ── Config ────────────────────────────────────────────────────
NICHE = "Fashion & Lifestyle"
PLATFORMS = ["Instagram", "YouTube", "TikTok", "LinkedIn", "Twitter/X", "Facebook"]
CONTENT_TYPES = ["Short Video", "Long Video", "Image Post", "Carousel", "Story", "Text Post", "Live"]
MONTHS = pd.date_range("2024-01-01", "2024-12-31", freq="MS").strftime("%b %Y").tolist()

# platform characteristics — realistic baselines
PLATFORM_PROFILE = {
    "Instagram": {
        "avg_reach_per_post": 4200, "avg_engagement_rate": 3.8,
        "cpm": 8.5, "cpc": 1.20, "ctr": 0.95,
        "follower_growth_rate": 2.8, "organic_reach_pct": 18,
        "best_content": ["Short Video", "Carousel", "Story"],
        "audience_quality": 7.2, "monetization_ease": 7.5,
    },
    "YouTube": {
        "avg_reach_per_post": 8500, "avg_engagement_rate": 4.9,
        "cpm": 12.0, "cpc": 2.10, "ctr": 0.62,
        "follower_growth_rate": 1.4, "organic_reach_pct": 42,
        "best_content": ["Long Video", "Short Video"],
        "audience_quality": 8.8, "monetization_ease": 9.0,
    },
    "TikTok": {
        "avg_reach_per_post": 12000, "avg_engagement_rate": 7.2,
        "cpm": 6.0, "cpc": 0.85, "ctr": 1.40,
        "follower_growth_rate": 6.5, "organic_reach_pct": 68,
        "best_content": ["Short Video", "Live"],
        "audience_quality": 5.8, "monetization_ease": 5.5,
    },
    "LinkedIn": {
        "avg_reach_per_post": 2800, "avg_engagement_rate": 2.1,
        "cpm": 18.0, "cpc": 4.50, "ctr": 0.45,
        "follower_growth_rate": 1.8, "organic_reach_pct": 28,
        "best_content": ["Text Post", "Carousel", "Long Video"],
        "audience_quality": 9.2, "monetization_ease": 6.0,
    },
    "Twitter/X": {
        "avg_reach_per_post": 3100, "avg_engagement_rate": 1.6,
        "cpm": 5.5, "cpc": 0.70, "ctr": 0.80,
        "follower_growth_rate": 2.1, "organic_reach_pct": 22,
        "best_content": ["Text Post", "Short Video"],
        "audience_quality": 6.4, "monetization_ease": 4.5,
    },
    "Facebook": {
        "avg_reach_per_post": 1800, "avg_engagement_rate": 1.2,
        "cpm": 9.0, "cpc": 1.60, "ctr": 0.72,
        "follower_growth_rate": 0.8, "organic_reach_pct": 8,
        "best_content": ["Long Video", "Image Post", "Live"],
        "audience_quality": 6.8, "monetization_ease": 7.0,
    },
}

# ── Generate Monthly Performance Data ─────────────────────────
rows = []
for platform, profile in PLATFORM_PROFILE.items():
    for i, month in enumerate(MONTHS):
        seasonal = 1 + 0.15 * np.sin(2 * np.pi * i / 12)
        noise = np.random.uniform(0.88, 1.12)

        posts = np.random.randint(8, 22)
        reach = int(profile["avg_reach_per_post"] * posts * seasonal * noise)
        eng_rate = round(profile["avg_engagement_rate"] * seasonal * noise, 2)
        eng_rate = max(0.5, min(15, eng_rate))
        engagements = int(reach * eng_rate / 100)
        followers_gained = int(reach * profile["follower_growth_rate"] / 100 * noise)
        ad_spend = round(np.random.uniform(3000, 8000) * noise, 2)
        impressions = int(reach * np.random.uniform(1.4, 2.2))
        clicks = int(impressions * profile["ctr"] / 100 * noise)
        conversions = int(clicks * np.random.uniform(0.02, 0.06))
        revenue = round(conversions * np.random.uniform(800, 2500), 2)
        roas = round(revenue / ad_spend, 2) if ad_spend > 0 else 0

        rows.append({
            "month": month, "platform": platform,
            "posts": posts, "reach": reach,
            "impressions": impressions, "engagements": engagements,
            "engagement_rate": eng_rate, "followers_gained": followers_gained,
            "ad_spend": ad_spend, "clicks": clicks,
            "conversions": conversions, "revenue": revenue, "roas": roas,
            "organic_reach_pct": profile["organic_reach_pct"],
            "cpm": round(ad_spend / impressions * 1000, 2),
            "cpc": round(ad_spend / max(clicks, 1), 2),
            "cost_per_conversion": round(ad_spend / max(conversions, 1), 2),
        })

df = pd.DataFrame(rows)
df.to_csv("data/platform_data.csv", index=False)
print(f"generated: {len(df)} rows ({len(PLATFORMS)} platforms × 12 months)")

# ── Platform Score Card ────────────────────────────────────────
summary = df.groupby("platform").agg(
    total_reach=("reach", "sum"),
    total_engagements=("engagements", "sum"),
    avg_eng_rate=("engagement_rate", "mean"),
    total_followers=("followers_gained", "sum"),
    total_spend=("ad_spend", "sum"),
    total_revenue=("revenue", "sum"),
    avg_roas=("roas", "mean"),
    avg_cpm=("cpm", "mean"),
    avg_cpc=("cpc", "mean"),
    avg_cpc_conv=("cost_per_conversion", "mean"),
    total_conversions=("conversions", "sum"),
).round(2).reset_index()

summary["reach_per_dollar"] = (summary["total_reach"] / summary["total_spend"]).round(2)
summary["engagement_per_dollar"] = (summary["total_engagements"] / summary["total_spend"]).round(2)
summary["follower_per_dollar"] = (summary["total_followers"] / summary["total_spend"]).round(2)

# platform score (weighted composite)
scaler = MinMaxScaler()
score_features = ["avg_eng_rate", "total_reach", "avg_roas", "reach_per_dollar",
                  "engagement_per_dollar", "total_followers"]
scores_norm = scaler.fit_transform(summary[score_features])
weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
summary["platform_score"] = (scores_norm * weights).sum(axis=1).round(3)
summary["platform_score"] = (summary["platform_score"] * 10).round(2)
summary = summary.sort_values("platform_score", ascending=False).reset_index(drop=True)
summary["rank"] = range(1, len(summary) + 1)

summary.to_csv("outputs/platform_scorecard.csv", index=False)

print("\nPlatform Scorecard:")
print(summary[["rank","platform","platform_score","avg_eng_rate","total_reach",
               "avg_roas","avg_cpm","reach_per_dollar"]].to_string(index=False))

# ── Content Type Analysis ──────────────────────────────────────
content_rows = []
for platform, profile in PLATFORM_PROFILE.items():
    for ct in CONTENT_TYPES:
        is_best = ct in profile["best_content"]
        base_eng = profile["avg_engagement_rate"]
        multiplier = np.random.uniform(1.3, 1.8) if is_best else np.random.uniform(0.4, 0.85)
        content_rows.append({
            "platform": platform,
            "content_type": ct,
            "avg_engagement_rate": round(base_eng * multiplier, 2),
            "avg_reach_multiplier": round(multiplier, 2),
            "is_recommended": is_best,
        })

content_df = pd.DataFrame(content_rows)
content_df.to_csv("outputs/content_type_analysis.csv", index=False)

# ── Investment Recommendation ──────────────────────────────────
budget = 50000  # monthly budget
rec = summary.copy()
rec["budget_allocation_pct"] = (rec["platform_score"] / rec["platform_score"].sum() * 100).round(1)
rec["recommended_budget"] = (rec["budget_allocation_pct"] / 100 * budget).round(0)
rec.to_csv("outputs/budget_recommendation.csv", index=False)

print("\nRecommended Budget Allocation (₹50,000/month):")
print(rec[["platform","platform_score","budget_allocation_pct","recommended_budget"]].to_string(index=False))

# ── Monthly Trends ─────────────────────────────────────────────
monthly = df.pivot_table(index="month", columns="platform", values="engagement_rate", aggfunc="mean")
monthly_reach = df.pivot_table(index="month", columns="platform", values="reach", aggfunc="sum")

# ── Dashboard ─────────────────────────────────────────────────
fig = plt.figure(figsize=(24, 18))
fig.suptitle(f"Social Media Platform Intelligence Report — {NICHE}", fontsize=20, fontweight="bold", y=0.98)
fig.patch.set_facecolor("#0d1117")
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.48, wspace=0.38)

bg = "#161b22"
border = "#30363d"
COLORS = {
    "Instagram": "#E1306C", "YouTube": "#FF0000", "TikTok": "#69C9D0",
    "LinkedIn": "#0077B5", "Twitter/X": "#1DA1F2", "Facebook": "#1877F2"
}

def style(ax, title):
    ax.set_facecolor(bg)
    ax.tick_params(colors="#8b949e", labelsize=8)
    ax.xaxis.label.set_color("#8b949e")
    ax.yaxis.label.set_color("#8b949e")
    ax.set_title(title, color="#e6edf3", fontweight="bold", fontsize=10, pad=10)
    for s in ax.spines.values():
        s.set_edgecolor(border)

# 1. Platform Score Bar
ax1 = fig.add_subplot(gs[0, 0])
style(ax1, "Overall Platform Score (0–10)")
colors = [COLORS[p] for p in summary["platform"]]
bars = ax1.barh(summary["platform"][::-1], summary["platform_score"][::-1], color=colors[::-1], height=0.55)
ax1.set_xlabel("Score")
ax1.set_xlim(0, 11)
for bar, val in zip(bars, summary["platform_score"][::-1]):
    ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
             f"{val:.1f}", va="center", color="#e6edf3", fontsize=9, fontweight="bold")

# 2. Engagement Rate by Platform
ax2 = fig.add_subplot(gs[0, 1])
style(ax2, "Avg Engagement Rate by Platform (%)")
bars2 = ax2.bar(summary["platform"], summary["avg_eng_rate"],
                color=[COLORS[p] for p in summary["platform"]], width=0.6)
ax2.set_ylabel("%")
ax2.tick_params(axis="x", rotation=25)
for bar, val in zip(bars2, summary["avg_eng_rate"]):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
             f"{val:.1f}%", ha="center", color="#e6edf3", fontsize=8, fontweight="bold")

# 3. ROAS by Platform
ax3 = fig.add_subplot(gs[0, 2])
style(ax3, "Avg ROAS by Platform")
bars3 = ax3.bar(summary["platform"], summary["avg_roas"],
                color=[COLORS[p] for p in summary["platform"]], width=0.6)
ax3.axhline(1, color="white", linestyle="--", linewidth=1, alpha=0.4, label="Break-even")
ax3.set_ylabel("ROAS")
ax3.legend(fontsize=8, facecolor=bg, labelcolor="#c9d1d9")
ax3.tick_params(axis="x", rotation=25)
for bar, val in zip(bars3, summary["avg_roas"]):
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02,
             f"{val:.1f}x", ha="center", color="#e6edf3", fontsize=8, fontweight="bold")

# 4. Monthly Engagement Rate Trend
ax4 = fig.add_subplot(gs[1, :2])
style(ax4, "Monthly Engagement Rate Trend (%)")
for platform in PLATFORMS:
    if platform in monthly.columns:
        ax4.plot(range(12), monthly[platform].values, marker="o", linewidth=2,
                 label=platform, color=COLORS[platform], markersize=4)
ax4.set_xticks(range(12))
ax4.set_xticklabels(MONTHS, rotation=35, ha="right", fontsize=7)
ax4.set_ylabel("%")
ax4.legend(fontsize=8, facecolor=bg, labelcolor="#c9d1d9", ncol=2)

# 5. Reach per Dollar (efficiency)
ax5 = fig.add_subplot(gs[1, 2])
style(ax5, "Reach per ₹1 Spent")
eff = summary.sort_values("reach_per_dollar", ascending=True)
ax5.barh(eff["platform"], eff["reach_per_dollar"],
         color=[COLORS[p] for p in eff["platform"]], height=0.55)
ax5.set_xlabel("Users Reached per ₹1")
for i, (_, row) in enumerate(eff.iterrows()):
    ax5.text(row["reach_per_dollar"]+0.01, i, f"{row['reach_per_dollar']:.2f}",
             va="center", color="#e6edf3", fontsize=8)

# 6. Budget Allocation Pie
ax6 = fig.add_subplot(gs[2, 0])
style(ax6, "Recommended Budget Allocation")
wedge_colors = [COLORS[p] for p in rec["platform"]]
wedges, texts, autotexts = ax6.pie(
    rec["budget_allocation_pct"], labels=rec["platform"],
    autopct="%1.1f%%", colors=wedge_colors, startangle=90,
    textprops={"color": "#c9d1d9", "fontsize": 8}
)
for at in autotexts:
    at.set_color("white")
    at.set_fontsize(8)

# 7. CPM comparison
ax7 = fig.add_subplot(gs[2, 1])
style(ax7, "Avg CPM (Cost per 1000 Impressions) ₹")
cpm_sorted = summary.sort_values("avg_cpm")
bar_colors = ["#3fb950" if v < 8 else "#ffa657" if v < 12 else "#f85149" for v in cpm_sorted["avg_cpm"]]
bars7 = ax7.barh(cpm_sorted["platform"], cpm_sorted["avg_cpm"], color=bar_colors, height=0.55)
ax7.set_xlabel("CPM (₹)")
for bar, val in zip(bars7, cpm_sorted["avg_cpm"]):
    ax7.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
             f"₹{val:.1f}", va="center", color="#e6edf3", fontsize=8)

# 8. Content type heatmap
ax8 = fig.add_subplot(gs[2, 2])
style(ax8, "Best Content Type per Platform")
pivot_ct = content_df.pivot_table(index="platform", columns="content_type",
                                   values="avg_engagement_rate", aggfunc="mean")
im = ax8.imshow(pivot_ct.values, cmap="YlOrRd", aspect="auto")
ax8.set_xticks(range(len(pivot_ct.columns)))
ax8.set_xticklabels(pivot_ct.columns, rotation=35, ha="right", fontsize=7, color="#8b949e")
ax8.set_yticks(range(len(pivot_ct.index)))
ax8.set_yticklabels(pivot_ct.index, fontsize=8, color="#8b949e")
plt.colorbar(im, ax=ax8, label="Eng Rate %")

for ax in fig.axes:
    ax.set_facecolor(bg)

plt.savefig("outputs/platform_intelligence_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print("\nDashboard saved.")

# ── Final Recommendation ───────────────────────────────────────
top3 = summary.head(3)
print("\n" + "="*55)
print(f"  PLATFORM INTELLIGENCE REPORT — {NICHE}")
print("="*55)
print(f"\nTop Platforms:")
for _, row in top3.iterrows():
    print(f"  #{int(row['rank'])} {row['platform']:15s} Score: {row['platform_score']:.1f}/10 | ROAS: {row['avg_roas']:.1f}x | Eng: {row['avg_eng_rate']:.1f}%")
print(f"\nHighest Engagement  : {summary.iloc[summary['avg_eng_rate'].values.argmax()]['platform']}")
print(f"Best ROAS           : {summary.iloc[summary['avg_roas'].values.argmax()]['platform']}")
print(f"Cheapest Reach      : {summary.iloc[summary['reach_per_dollar'].values.argmax()]['platform']}")
print(f"Most Followers/₹    : {summary.iloc[summary['follower_per_dollar'].values.argmax()]['platform']}")
print("="*55)

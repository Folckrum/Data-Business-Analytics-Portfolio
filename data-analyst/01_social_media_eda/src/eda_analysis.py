import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

np.random.seed(42)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")


def generate_data(n=1200):
    platforms = ["Instagram", "Twitter", "LinkedIn", "Facebook"]
    post_types = ["Video", "Image", "Text", "Carousel"]
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    df = pd.DataFrame({
        "post_id": range(1, n + 1),
        "platform": np.random.choice(platforms, n, p=[0.35, 0.30, 0.20, 0.15]),
        "post_type": np.random.choice(post_types, n, p=[0.30, 0.35, 0.20, 0.15]),
        "day_posted": np.random.choice(days, n),
        "hour_posted": np.random.randint(6, 23, n),
        "reach": np.random.randint(500, 50000, n),
        "impressions": np.random.randint(600, 80000, n),
        "likes": np.random.randint(10, 5000, n),
        "comments": np.random.randint(0, 500, n),
        "shares": np.random.randint(0, 300, n),
        "followers_at_post": np.random.randint(1000, 100000, n),
    })

    video_mask = df["post_type"] == "Video"
    df.loc[video_mask, "likes"] = (df.loc[video_mask, "likes"] * 2.3).astype(int)
    df.loc[video_mask, "shares"] = (df.loc[video_mask, "shares"] * 1.8).astype(int)

    df["engagement_rate"] = (
        (df["likes"] + df["comments"] + df["shares"]) / df["reach"] * 100
    ).round(2)

    df["date"] = pd.date_range(start="2023-01-01", periods=n, freq="6h")
    return df


def plot_engagement_distribution(df):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Engagement Metrics Distribution", fontsize=15, fontweight="bold")
    for ax, col in zip(axes, ["likes", "shares", "comments"]):
        sns.histplot(df[col], ax=ax, kde=True, bins=40, color="#4C72B0")
        ax.set_title(f"{col.capitalize()} Distribution")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/01_engagement_distribution.png", dpi=150)
    plt.close()
    print("Saved: 01_engagement_distribution.png")


def plot_platform_comparison(df):
    stats = df.groupby("platform").agg(
        avg_engagement=("engagement_rate", "mean"),
        avg_reach=("reach", "mean")
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Platform Performance Comparison", fontsize=15, fontweight="bold")
    sns.barplot(data=stats, x="platform", y="avg_engagement", ax=axes[0], palette="Blues_d")
    axes[0].set_title("Avg Engagement Rate (%)")
    sns.barplot(data=stats, x="platform", y="avg_reach", ax=axes[1], palette="Greens_d")
    axes[1].set_title("Avg Reach")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/02_platform_comparison.png", dpi=150)
    plt.close()
    print("Saved: 02_platform_comparison.png")


def plot_post_type_analysis(df):
    type_stats = df.groupby("post_type")["engagement_rate"].mean().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(type_stats.index, type_stats.values,
                   color=["#e74c3c", "#3498db", "#2ecc71", "#f39c12"])
    plt.title("Avg Engagement Rate by Post Type", fontsize=14, fontweight="bold")
    plt.ylabel("Avg Engagement Rate (%)")
    for bar, val in zip(bars, type_stats.values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{val:.2f}%", ha="center", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/03_post_type_analysis.png", dpi=150)
    plt.close()
    print("Saved: 03_post_type_analysis.png")


def plot_heatmap_day_hour(df):
    pivot = df.pivot_table(values="engagement_rate", index="day_posted",
                           columns="hour_posted", aggfunc="mean")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(day_order)
    plt.figure(figsize=(16, 6))
    sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.5)
    plt.title("Engagement Rate Heatmap: Day vs Hour Posted", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/04_day_hour_heatmap.png", dpi=150)
    plt.close()
    print("Saved: 04_day_hour_heatmap.png")


def plot_correlation_matrix(df):
    numeric_cols = ["reach", "impressions", "likes", "comments", "shares", "engagement_rate"]
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Correlation Matrix — Engagement Metrics", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/05_correlation_matrix.png", dpi=150)
    plt.close()
    print("Saved: 05_correlation_matrix.png")


def print_summary(df):
    print("\n" + "=" * 50)
    print("   SOCIAL MEDIA EDA — KEY INSIGHTS")
    print("=" * 50)
    print(f"Total Posts        : {len(df):,}")
    print(f"Avg Engagement     : {df['engagement_rate'].mean():.2f}%")
    print(f"Top Platform       : {df.groupby('platform')['engagement_rate'].mean().idxmax()}")
    print(f"Top Post Type      : {df.groupby('post_type')['engagement_rate'].mean().idxmax()}")
    print(f"Best Day           : {df.groupby('day_posted')['engagement_rate'].mean().idxmax()}")
    print(f"Best Hour          : {df.groupby('hour_posted')['engagement_rate'].mean().idxmax()}:00")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print("Running Social Media EDA...")
    df = generate_data()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/social_media_data.csv", index=False)
    print(f"Dataset: {len(df)} rows saved to data/social_media_data.csv")
    plot_engagement_distribution(df)
    plot_platform_comparison(df)
    plot_post_type_analysis(df)
    plot_heatmap_day_hour(df)
    plot_correlation_matrix(df)
    print_summary(df)
    print("All outputs saved to /outputs/")

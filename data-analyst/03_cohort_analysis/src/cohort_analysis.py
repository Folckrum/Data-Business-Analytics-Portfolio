import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

np.random.seed(7)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_user_data(n_users=3000, n_orders=12000):
    user_ids = range(1, n_users + 1)
    signup_dates = pd.to_datetime(
        np.random.choice(pd.date_range("2023-01-01", "2023-06-30"), n_users)
    )
    users = pd.DataFrame({"user_id": user_ids, "signup_date": signup_dates})

    order_user_ids = np.random.choice(user_ids, n_orders)
    order_dates = pd.to_datetime(
        np.random.choice(pd.date_range("2023-01-01", "2023-12-31"), n_orders)
    )
    orders = pd.DataFrame({
        "order_id": range(1, n_orders + 1),
        "user_id": order_user_ids,
        "order_date": order_dates,
        "order_value": np.random.uniform(50, 2000, n_orders).round(2),
    })

    df = orders.merge(users, on="user_id")
    df = df[df["order_date"] >= df["signup_date"]]
    return df


def build_cohort_table(df):
    df["cohort_month"] = df["signup_date"].dt.to_period("M")
    df["order_month"] = df["order_date"].dt.to_period("M")
    df["months_since_signup"] = (
        df["order_month"].astype(int) - df["cohort_month"].astype(int)
    )
    df = df[df["months_since_signup"] >= 0]

    cohort_data = df.groupby(["cohort_month", "months_since_signup"])["user_id"].nunique().reset_index()
    cohort_data.columns = ["cohort_month", "months_since_signup", "active_users"]

    cohort_sizes = cohort_data[cohort_data["months_since_signup"] == 0].set_index("cohort_month")["active_users"]
    cohort_pivot = cohort_data.pivot_table(index="cohort_month", columns="months_since_signup", values="active_users")
    retention = cohort_pivot.divide(cohort_sizes, axis=0).round(3) * 100
    return retention, cohort_sizes


def plot_retention_heatmap(retention):
    plt.figure(figsize=(14, 7))
    sns.heatmap(
        retention,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        linewidths=0.5,
        vmin=0,
        vmax=100,
        cbar_kws={"label": "Retention Rate (%)"},
    )
    plt.title("User Retention Cohort Analysis — Monthly Retention Rates (%)",
              fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Months Since Signup", fontsize=12)
    plt.ylabel("Cohort (Signup Month)", fontsize=12)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/01_cohort_retention_heatmap.png", dpi=150)
    plt.close()
    print("Saved: 01_cohort_retention_heatmap.png")


def plot_retention_curves(retention):
    plt.figure(figsize=(12, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(retention)))

    for (cohort, row), color in zip(retention.iterrows(), colors):
        valid = row.dropna()
        plt.plot(valid.index, valid.values, marker="o", label=str(cohort),
                 color=color, linewidth=2, markersize=5)

    plt.title("Retention Curves by Cohort", fontsize=14, fontweight="bold")
    plt.xlabel("Months Since Signup")
    plt.ylabel("Retention Rate (%)")
    plt.legend(title="Cohort Month", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/02_retention_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: 02_retention_curves.png")


def plot_cohort_sizes(cohort_sizes):
    plt.figure(figsize=(10, 5))
    bars = plt.bar(cohort_sizes.index.astype(str), cohort_sizes.values, color="#3498db", edgecolor="white")
    plt.title("Cohort Sizes — New Users per Month", fontsize=14, fontweight="bold")
    plt.xlabel("Cohort Month")
    plt.ylabel("Number of Users")
    plt.xticks(rotation=30, ha="right")
    for bar, val in zip(bars, cohort_sizes.values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                 str(val), ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/03_cohort_sizes.png", dpi=150)
    plt.close()
    print("Saved: 03_cohort_sizes.png")


def print_summary(retention, cohort_sizes):
    print("\n" + "=" * 50)
    print("    COHORT ANALYSIS — INSIGHTS SUMMARY")
    print("=" * 50)
    print(f"Total Cohorts Analyzed : {len(retention)}")
    print(f"Total Users (base)     : {cohort_sizes.sum():,}")
    avg_m1 = retention[1].mean() if 1 in retention.columns else 0
    avg_m3 = retention[3].mean() if 3 in retention.columns else 0
    avg_m6 = retention[6].mean() if 6 in retention.columns else 0
    print(f"Avg Month-1 Retention  : {avg_m1:.1f}%")
    print(f"Avg Month-3 Retention  : {avg_m3:.1f}%")
    print(f"Avg Month-6 Retention  : {avg_m6:.1f}%")
    best = cohort_sizes.idxmax()
    print(f"Largest Cohort         : {best} ({cohort_sizes[best]:,} users)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print("Running Cohort Analysis...")
    df = generate_user_data()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/user_orders.csv", index=False)
    print(f"Dataset: {len(df)} orders saved")

    retention, cohort_sizes = build_cohort_table(df)

    plot_retention_heatmap(retention)
    plot_retention_curves(retention)
    plot_cohort_sizes(cohort_sizes)
    print_summary(retention, cohort_sizes)
    print("Done.")

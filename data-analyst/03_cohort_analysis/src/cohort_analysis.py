import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

np.random.seed(7)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

n_users = 3000
user_ids = range(1, n_users+1)
signup_dates = pd.to_datetime(np.random.choice(pd.date_range("2023-01-01", "2023-06-30"), n_users))
users = pd.DataFrame({"user_id": user_ids, "signup_date": signup_dates})

n_orders = 12000
orders = pd.DataFrame({
    "order_id": range(1, n_orders+1),
    "user_id": np.random.choice(list(user_ids), n_orders),
    "order_date": pd.to_datetime(np.random.choice(pd.date_range("2023-01-01", "2023-12-31"), n_orders)),
    "order_value": np.random.uniform(50, 2000, n_orders).round(2),
})

df = orders.merge(users, on="user_id")
df = df[df["order_date"] >= df["signup_date"]]
df.to_csv("data/user_orders.csv", index=False)

df["cohort"] = df["signup_date"].dt.to_period("M")
df["order_month"] = df["order_date"].dt.to_period("M")
df["months_since"] = (df["order_month"].astype(int) - df["cohort"].astype(int))
df = df[df["months_since"] >= 0]

cohort_data = df.groupby(["cohort","months_since"])["user_id"].nunique().reset_index()
cohort_data.columns = ["cohort","months_since","users"]

sizes = cohort_data[cohort_data["months_since"]==0].set_index("cohort")["users"]
pivot = cohort_data.pivot_table(index="cohort", columns="months_since", values="users")
retention = (pivot.divide(sizes, axis=0) * 100).round(1)

plt.figure(figsize=(14, 7))
sns.heatmap(retention, annot=True, fmt=".1f", cmap="RdYlGn", linewidths=0.5, vmin=0, vmax=100,
            cbar_kws={"label": "Retention Rate (%)"})
plt.title("Monthly User Retention by Cohort (%)", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Months Since Signup")
plt.ylabel("Cohort (Signup Month)")
plt.tight_layout()
plt.savefig("outputs/01_retention_heatmap.png", dpi=150)
plt.close()

plt.figure(figsize=(12, 6))
colors = plt.cm.tab10(np.linspace(0, 1, len(retention)))
for (cohort, row), color in zip(retention.iterrows(), colors):
    v = row.dropna()
    plt.plot(v.index, v.values, marker="o", label=str(cohort), color=color, linewidth=2, markersize=5)
plt.title("Retention Curves by Cohort", fontsize=14, fontweight="bold")
plt.xlabel("Months Since Signup")
plt.ylabel("Retention Rate (%)")
plt.legend(title="Cohort", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/02_retention_curves.png", dpi=150, bbox_inches="tight")
plt.close()

plt.figure(figsize=(10, 5))
bars = plt.bar(sizes.index.astype(str), sizes.values, color="#3498db", edgecolor="white")
plt.title("New Users per Cohort Month", fontsize=14, fontweight="bold")
plt.xlabel("Cohort Month")
plt.ylabel("Users")
plt.xticks(rotation=30, ha="right")
for bar, val in zip(bars, sizes.values):
    plt.text(bar.get_x()+bar.get_width()/2, bar.get_height()+3, str(val), ha="center", fontsize=9)
plt.tight_layout()
plt.savefig("outputs/03_cohort_sizes.png", dpi=150)
plt.close()

print(f"cohorts: {len(retention)}")
print(f"avg month-1 retention: {retention[1].mean():.1f}%" if 1 in retention.columns else "")
print(f"avg month-3 retention: {retention[3].mean():.1f}%" if 3 in retention.columns else "")

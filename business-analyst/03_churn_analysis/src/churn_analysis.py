import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import LabelEncoder
import os

np.random.seed(42)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)
sns.set_theme(style="whitegrid")

n = 5000
plans = ["Basic", "Standard", "Premium"]
channels = ["Online", "Retail", "App"]
regions = ["North", "South", "East", "West"]

df = pd.DataFrame({
    "customer_id": [f"CUST{i:05d}" for i in range(1, n+1)],
    "plan": np.random.choice(plans, n, p=[0.40, 0.35, 0.25]),
    "region": np.random.choice(regions, n),
    "channel": np.random.choice(channels, n),
    "tenure_months": np.random.randint(1, 60, n),
    "monthly_charges": np.random.uniform(200, 2000, n).round(2),
    "num_products": np.random.randint(1, 6, n),
    "support_calls": np.random.randint(0, 15, n),
    "late_payments": np.random.randint(0, 8, n),
    "avg_session_days": np.random.uniform(1, 30, n).round(1),
    "complaints_6m": np.random.randint(0, 5, n),
})

# churn logic — short tenure + high support calls + late payments → more likely to churn
churn_score = (
    (df["tenure_months"] < 12).astype(int) * 0.3 +
    (df["support_calls"] > 7).astype(int) * 0.25 +
    (df["late_payments"] > 3).astype(int) * 0.25 +
    (df["plan"] == "Basic").astype(int) * 0.1 +
    (df["complaints_6m"] > 2).astype(int) * 0.1
)
df["churned"] = (churn_score + np.random.uniform(0, 0.3, n) > 0.4).astype(int)
df.to_csv("data/churn_data.csv", index=False)

churn_rate = df["churned"].mean() * 100
print(f"overall churn rate: {churn_rate:.1f}%")

# churn by plan
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("Customer Churn Analysis", fontsize=16, fontweight="bold")

plan_churn = df.groupby("plan")["churned"].mean() * 100
axes[0,0].bar(plan_churn.index, plan_churn.values, color=["#e74c3c","#f39c12","#2ecc71"])
axes[0,0].axhline(churn_rate, color="navy", linestyle="--", linewidth=1.5, label=f"avg {churn_rate:.1f}%")
axes[0,0].set_title("Churn Rate by Plan", fontweight="bold")
axes[0,0].set_ylabel("%")
axes[0,0].legend(fontsize=8)

# churn by tenure bucket
df["tenure_bucket"] = pd.cut(df["tenure_months"], bins=[0,6,12,24,36,60],
                              labels=["0-6m","7-12m","13-24m","25-36m","37-60m"])
ten_churn = df.groupby("tenure_bucket", observed=True)["churned"].mean() * 100
axes[0,1].plot(ten_churn.index.astype(str), ten_churn.values, marker="o", color="#e74c3c", linewidth=2.5, markersize=8)
axes[0,1].set_title("Churn Rate by Tenure", fontweight="bold")
axes[0,1].set_ylabel("%")
axes[0,1].set_xlabel("Tenure")

# support calls vs churn
axes[0,2].boxplot([df[df["churned"]==0]["support_calls"], df[df["churned"]==1]["support_calls"]],
                   labels=["Stayed","Churned"])
axes[0,2].set_title("Support Calls: Stayed vs Churned", fontweight="bold")
axes[0,2].set_ylabel("Support Calls")

# late payments vs churn
lp_churn = df.groupby("late_payments")["churned"].mean() * 100
axes[1,0].bar(lp_churn.index, lp_churn.values, color="#9b59b6")
axes[1,0].set_title("Churn Rate by Late Payments", fontweight="bold")
axes[1,0].set_ylabel("%")
axes[1,0].set_xlabel("# Late Payments")

# region churn
reg_churn = df.groupby("region")["churned"].mean() * 100
axes[1,1].bar(reg_churn.index, reg_churn.values, color=["#3498db","#e67e22","#1abc9c","#e74c3c"])
axes[1,1].axhline(churn_rate, color="navy", linestyle="--", linewidth=1.5)
axes[1,1].set_title("Churn Rate by Region", fontweight="bold")
axes[1,1].set_ylabel("%")

# monthly charges dist — churned vs not
axes[1,2].hist(df[df["churned"]==0]["monthly_charges"], bins=30, alpha=0.6, color="#2ecc71", label="Stayed")
axes[1,2].hist(df[df["churned"]==1]["monthly_charges"], bins=30, alpha=0.6, color="#e74c3c", label="Churned")
axes[1,2].set_title("Monthly Charges Distribution", fontweight="bold")
axes[1,2].set_xlabel("Monthly Charges (₹)")
axes[1,2].legend()

plt.tight_layout()
plt.savefig("outputs/01_churn_overview.png", dpi=150, bbox_inches="tight")
plt.close()

# ML model — Random Forest
le = LabelEncoder()
df_ml = df.copy()
for col in ["plan", "region", "channel", "tenure_bucket"]:
    df_ml[col] = le.fit_transform(df_ml[col].astype(str))

features = ["plan","region","channel","tenure_months","monthly_charges",
            "num_products","support_calls","late_payments","avg_session_days","complaints_6m"]
X = df_ml[features]
y = df_ml["churned"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_prob)
print(f"\nRandom Forest AUC: {auc:.3f}")
print(classification_report(y_test, y_pred))

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Churn Prediction Model — Random Forest", fontsize=14, fontweight="bold")

# feature importance
imp = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=True)
axes[0].barh(imp.index, imp.values, color="#3498db")
axes[0].set_title("Feature Importance", fontweight="bold")

# confusion matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[1],
            xticklabels=["Stayed","Churned"], yticklabels=["Stayed","Churned"])
axes[1].set_title(f"Confusion Matrix", fontweight="bold")
axes[1].set_ylabel("Actual")
axes[1].set_xlabel("Predicted")

# ROC curve
fpr, tpr, _ = roc_curve(y_test, y_prob)
axes[2].plot(fpr, tpr, color="#e74c3c", linewidth=2.5, label=f"AUC = {auc:.3f}")
axes[2].plot([0,1], [0,1], "k--", linewidth=1)
axes[2].set_title("ROC Curve", fontweight="bold")
axes[2].set_xlabel("False Positive Rate")
axes[2].set_ylabel("True Positive Rate")
axes[2].legend()

plt.tight_layout()
plt.savefig("outputs/02_model_results.png", dpi=150, bbox_inches="tight")
plt.close()

# high risk customers — top 10% churn probability
df_ml["churn_prob"] = rf.predict_proba(X)[:, 1]
df["churn_prob"] = df_ml["churn_prob"].values
high_risk = df[df["churn_prob"] >= df["churn_prob"].quantile(0.90)].copy()
high_risk = high_risk.sort_values("churn_prob", ascending=False)
high_risk[["customer_id","plan","tenure_months","support_calls","late_payments","churn_prob"]].to_csv(
    "reports/high_risk_customers.csv", index=False
)

report = f"""CHURN ANALYSIS REPORT — FY 2023
Total Customers : {len(df):,}
Churned         : {df['churned'].sum():,}
Churn Rate      : {churn_rate:.1f}%

TOP CHURN DRIVERS (by feature importance)
- Support calls (too many = frustration signal)
- Late payments (financial stress → likely to cancel)
- Tenure (first 12 months are highest risk)
- Complaints in last 6 months

SEGMENT BREAKDOWN
- Basic plan churn rate  : {plan_churn['Basic']:.1f}%
- Premium plan churn rate: {plan_churn['Premium']:.1f}%
- Highest risk region    : {reg_churn.idxmax()} ({reg_churn.max():.1f}%)

MODEL PERFORMANCE
- Algorithm  : Random Forest (100 trees, max_depth=6)
- AUC Score  : {auc:.3f}
- High-risk customers flagged (top 10%): {len(high_risk):,}

RECOMMENDATIONS
1. Trigger retention campaign at month 6 and 12 (peak churn windows)
2. Proactively reach out to customers with 3+ support calls in 30 days
3. Offer plan upgrade discount to Basic customers at 6-month mark
4. Flag customers with 2+ late payments for account manager review
"""
with open("reports/churn_report.txt", "w") as f:
    f.write(report)
print(report)

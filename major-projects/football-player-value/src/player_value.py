import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
os._exit if False else None
import os
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# ── Generate realistic player data ────────────────────────────
n = 800
positions = ["ST", "CAM", "CM", "LW", "RW", "CB", "LB", "RB", "GK", "CDM"]
leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
nationalities = ["English", "Spanish", "French", "German", "Brazilian",
                 "Argentine", "Portuguese", "Dutch", "Italian", "Belgian"]
foot = ["Right", "Left"]

pos_base = {
    "ST": 35, "CAM": 32, "LW": 30, "RW": 30,
    "CM": 25, "CDM": 22, "CB": 20,
    "LB": 18, "RB": 18, "GK": 15,
}
league_mult = {
    "Premier League": 1.45, "La Liga": 1.30,
    "Bundesliga": 1.15, "Serie A": 1.10, "Ligue 1": 0.95,
}

players = []
for i in range(n):
    pos = np.random.choice(positions)
    league = np.random.choice(leagues)
    age = int(np.random.normal(24, 4))
    age = max(16, min(38, age))

    # peak age curve — peaks around 25-27
    age_factor = 1 - abs(age - 26) * 0.035
    age_factor = max(0.3, age_factor)

    goals = int(np.random.poisson(pos_base[pos] * 0.6)) if pos in ["ST","LW","RW","CAM"] else int(np.random.poisson(5))
    assists = int(np.random.poisson(pos_base[pos] * 0.4)) if pos in ["CAM","LW","RW","CM"] else int(np.random.poisson(3))
    appearances = np.random.randint(20, 45)
    goals_per_90 = round(goals / max(appearances, 1) * 90 / 90, 2)
    assists_per_90 = round(assists / max(appearances, 1) * 90 / 90, 2)
    rating = round(np.random.normal(7.0, 0.6), 1)
    rating = max(5.5, min(9.5, rating))
    contract_years = np.random.randint(1, 5)
    international = int(np.random.random() < 0.35)
    int_caps = int(np.random.poisson(18)) if international else 0
    weeks_injured = int(np.random.poisson(2))
    pass_accuracy = round(np.random.normal(82, 7), 1)
    pass_accuracy = max(60, min(96, pass_accuracy))
    dribbles = round(np.random.uniform(0.5, 4.5), 1)
    tackles = round(np.random.uniform(0.5, 4.0), 1)

    # market value formula — position base * age curve * league * performance
    base = pos_base[pos]
    perf_boost = (goals * 0.8 + assists * 0.5 + (rating - 6.5) * 3)
    value = base * age_factor * league_mult[league] * (1 + perf_boost / 60)
    value += international * np.random.uniform(2, 8)
    value -= weeks_injured * 0.3
    value = max(0.5, value) * np.random.uniform(0.85, 1.15)  # noise

    players.append({
        "name": f"Player_{i+1:04d}",
        "age": age,
        "position": pos,
        "league": league,
        "nationality": np.random.choice(nationalities),
        "preferred_foot": np.random.choice(foot, p=[0.72, 0.28]),
        "appearances": appearances,
        "goals": goals,
        "assists": assists,
        "goals_per_90": goals_per_90,
        "assists_per_90": assists_per_90,
        "avg_rating": rating,
        "pass_accuracy": pass_accuracy,
        "dribbles_per_90": dribbles,
        "tackles_per_90": tackles,
        "contract_years_left": contract_years,
        "international": international,
        "int_caps": int_caps,
        "weeks_injured": weeks_injured,
        "market_value_m": round(value, 2),
    })

df = pd.DataFrame(players)
df.to_csv("data/players.csv", index=False)
print(f"players: {len(df)} | avg value: €{df['market_value_m'].mean():.1f}M | max: €{df['market_value_m'].max():.1f}M")

# ── Feature Engineering ───────────────────────────────────────
le_pos = LabelEncoder()
le_league = LabelEncoder()
le_nat = LabelEncoder()
le_foot = LabelEncoder()

df["pos_enc"] = le_pos.fit_transform(df["position"])
df["league_enc"] = le_league.fit_transform(df["league"])
df["nat_enc"] = le_nat.fit_transform(df["nationality"])
df["foot_enc"] = le_foot.fit_transform(df["preferred_foot"])
df["age_squared"] = df["age"] ** 2
df["goal_contribution"] = df["goals"] + df["assists"]
df["contribution_per_90"] = df["goals_per_90"] + df["assists_per_90"]
df["prime_age"] = ((df["age"] >= 23) & (df["age"] <= 28)).astype(int)

features = [
    "age", "age_squared", "pos_enc", "league_enc", "nat_enc", "foot_enc",
    "appearances", "goals", "assists", "goals_per_90", "assists_per_90",
    "avg_rating", "pass_accuracy", "dribbles_per_90", "tackles_per_90",
    "contract_years_left", "international", "int_caps",
    "weeks_injured", "goal_contribution", "contribution_per_90", "prime_age",
]

X = df[features]
y = df["market_value_m"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ── Model ─────────────────────────────────────────────────────
model = GradientBoostingRegressor(
    n_estimators=300, max_depth=4,
    learning_rate=0.05, subsample=0.8,
    random_state=42
)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
cv = cross_val_score(model, X, y, cv=5, scoring="r2")

print(f"\nModel Performance:")
print(f"  R² Score     : {r2:.3f}")
print(f"  MAE          : €{mae:.2f}M")
print(f"  CV R² (5-fold): {cv.mean():.3f} ± {cv.std():.3f}")

# ── Predictions ───────────────────────────────────────────────
df["predicted_value_m"] = model.predict(X).round(2)
df["value_gap_m"] = (df["predicted_value_m"] - df["market_value_m"]).round(2)
df["undervalued"] = df["value_gap_m"] > 3

undervalued = df[df["undervalued"]].sort_values("value_gap_m", ascending=False).head(15)
overvalued = df[df["value_gap_m"] < -3].sort_values("value_gap_m").head(10)

undervalued[["name","position","league","age","goals","assists","avg_rating","market_value_m","predicted_value_m","value_gap_m"]].to_csv("outputs/undervalued_players.csv", index=False)
overvalued[["name","position","league","age","goals","assists","avg_rating","market_value_m","predicted_value_m","value_gap_m"]].to_csv("outputs/overvalued_players.csv", index=False)

# position value summary
pos_summary = df.groupby("position").agg(
    avg_actual=("market_value_m","mean"),
    avg_predicted=("predicted_value_m","mean"),
    count=("name","count"),
    avg_goals=("goals","mean"),
    avg_rating=("avg_rating","mean"),
).round(2).reset_index().sort_values("avg_actual", ascending=False)
pos_summary.to_csv("outputs/position_summary.csv", index=False)

league_summary = df.groupby("league").agg(
    avg_value=("market_value_m","mean"),
    total_value=("market_value_m","sum"),
    count=("name","count"),
).round(2).reset_index().sort_values("avg_value", ascending=False)

# feature importance
imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False).head(12)

# ── Dashboard ─────────────────────────────────────────────────
fig = plt.figure(figsize=(22, 16))
fig.suptitle("Football Player Market Value Predictor", fontsize=20, fontweight="bold", y=0.98)
fig.patch.set_facecolor("#0d1117")
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

txt = {"color": "#c9d1d9"}
bg = "#161b22"
border = "#30363d"

def style_ax(ax, title):
    ax.set_facecolor(bg)
    ax.tick_params(colors="#8b949e")
    ax.xaxis.label.set_color("#8b949e")
    ax.yaxis.label.set_color("#8b949e")
    ax.set_title(title, color="#e6edf3", fontweight="bold", fontsize=11, pad=10)
    for spine in ax.spines.values():
        spine.set_edgecolor(border)

# 1. Actual vs Predicted scatter
ax1 = fig.add_subplot(gs[0, :2])
style_ax(ax1, "Actual vs Predicted Market Value")
sc = ax1.scatter(y_test, y_pred, alpha=0.6, c=y_pred, cmap="plasma", s=35, edgecolors="none")
lims = [0, max(y_test.max(), y_pred.max()) + 5]
ax1.plot(lims, lims, "w--", linewidth=1.5, alpha=0.5, label="Perfect prediction")
ax1.set_xlabel("Actual Value (€M)")
ax1.set_ylabel("Predicted Value (€M)")
ax1.legend(fontsize=9, facecolor=bg, labelcolor="#c9d1d9")
plt.colorbar(sc, ax=ax1, label="Predicted (€M)")
ax1.text(0.05, 0.90, f"R² = {r2:.3f}  |  MAE = €{mae:.2f}M",
         transform=ax1.transAxes, color="#58a6ff", fontsize=10, fontweight="bold")

# 2. Feature Importance
ax2 = fig.add_subplot(gs[0, 2])
style_ax(ax2, "Top Feature Importances")
colors_imp = plt.cm.Blues(np.linspace(0.4, 0.9, len(imp)))[::-1]
ax2.barh(imp.index[::-1], imp.values[::-1], color=colors_imp)
ax2.set_xlabel("Importance")

# 3. Value by Position
ax3 = fig.add_subplot(gs[1, 0])
style_ax(ax3, "Avg Market Value by Position (€M)")
pos_plot = pos_summary.sort_values("avg_actual", ascending=True)
colors_pos = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(pos_plot)))
ax3.barh(pos_plot["position"], pos_plot["avg_actual"], color=colors_pos)
ax3.set_xlabel("Avg Value (€M)")
for i, (_, row) in enumerate(pos_plot.iterrows()):
    ax3.text(row["avg_actual"] + 0.3, i, f"€{row['avg_actual']:.1f}M", va="center", color="#c9d1d9", fontsize=8)

# 4. Value by League
ax4 = fig.add_subplot(gs[1, 1])
style_ax(ax4, "Avg Market Value by League (€M)")
colors_lg = ["#f78166","#ffa657","#d2a8ff","#79c0ff","#56d364"]
bars = ax4.bar(league_summary["league"], league_summary["avg_value"], color=colors_lg)
ax4.set_ylabel("Avg Value (€M)")
ax4.tick_params(axis="x", rotation=20)
for bar, val in zip(bars, league_summary["avg_value"]):
    ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
             f"€{val:.1f}M", ha="center", color="#c9d1d9", fontsize=8, fontweight="bold")

# 5. Age vs Value scatter with trend
ax5 = fig.add_subplot(gs[1, 2])
style_ax(ax5, "Age vs Market Value")
sc2 = ax5.scatter(df["age"], df["market_value_m"], alpha=0.4, c=df["avg_rating"],
                  cmap="YlOrRd", s=20, edgecolors="none")
z = np.polyfit(df["age"], df["market_value_m"], 2)
p = np.poly1d(z)
age_range = np.linspace(df["age"].min(), df["age"].max(), 100)
ax5.plot(age_range, p(age_range), "w--", linewidth=2, label="Trend")
ax5.set_xlabel("Age")
ax5.set_ylabel("Value (€M)")
ax5.legend(fontsize=8, facecolor=bg, labelcolor="#c9d1d9")
plt.colorbar(sc2, ax=ax5, label="Avg Rating")

# 6. Top undervalued
ax6 = fig.add_subplot(gs[2, :2])
style_ax(ax6, "Top 12 Undervalued Players (Model Value > Market Value)")
top_under = undervalued.head(12).reset_index(drop=True)
x = range(len(top_under))
width = 0.38
bars1 = ax6.bar([i - width/2 for i in x], top_under["market_value_m"], width=width,
                label="Market Value", color="#f85149", alpha=0.85)
bars2 = ax6.bar([i + width/2 for i in x], top_under["predicted_value_m"], width=width,
                label="Model Value", color="#3fb950", alpha=0.85)
ax6.set_xticks(list(x))
ax6.set_xticklabels([f"{r['position']}\n{r['league'][:3]}" for _, r in top_under.iterrows()],
                    fontsize=7, color="#8b949e")
ax6.set_ylabel("Value (€M)")
ax6.legend(fontsize=9, facecolor=bg, labelcolor="#c9d1d9")
for i, (_, row) in enumerate(top_under.iterrows()):
    ax6.text(i + width/2, row["predicted_value_m"] + 0.2,
             f"+€{row['value_gap_m']:.1f}M", ha="center", color="#3fb950", fontsize=7, fontweight="bold")

# 7. Value distribution
ax7 = fig.add_subplot(gs[2, 2])
style_ax(ax7, "Market Value Distribution")
ax7.hist(df["market_value_m"], bins=40, color="#388bfd", alpha=0.8, edgecolor="none")
ax7.axvline(df["market_value_m"].mean(), color="#f85149", linewidth=2,
            label=f"Mean €{df['market_value_m'].mean():.1f}M")
ax7.axvline(df["market_value_m"].median(), color="#ffa657", linewidth=2,
            label=f"Median €{df['market_value_m'].median():.1f}M")
ax7.set_xlabel("Value (€M)")
ax7.set_ylabel("Players")
ax7.legend(fontsize=8, facecolor=bg, labelcolor="#c9d1d9")

for ax in fig.axes:
    ax.set_facecolor(bg)

plt.savefig("outputs/football_value_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print("\nDashboard saved.")

# ── Print Outputs ─────────────────────────────────────────────
print("\nTop 10 Undervalued Players:")
print(undervalued[["name","position","league","age","goals","market_value_m","predicted_value_m","value_gap_m"]].head(10).to_string(index=False))

print("\nPosition Value Summary:")
print(pos_summary[["position","avg_actual","avg_goals","avg_rating","count"]].to_string(index=False))

print("\nLeague Value Summary:")
print(league_summary.to_string(index=False))

print(f"\nTop Feature: {imp.index[0]} ({imp.values[0]:.3f})")
print(f"Undervalued players found: {df['undervalued'].sum()}")
print(f"Overvalued players found: {len(overvalued)}")

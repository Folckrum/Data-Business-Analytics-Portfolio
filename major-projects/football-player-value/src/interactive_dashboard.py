import sys, numpy as np, pandas as pd, plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
sys.path.insert(0, "../../shared")
from dash_template import page, BASE

df = pd.read_csv("data/players.csv")
for col, new in [("position", "pos_enc"), ("league", "league_enc"), ("nationality", "nat_enc"), ("preferred_foot", "foot_enc")]:
    df[new] = LabelEncoder().fit_transform(df[col])
df["age_squared"] = df["age"] ** 2
df["goal_contribution"] = df["goals"] + df["assists"]
df["contribution_per_90"] = df["goals_per_90"] + df["assists_per_90"]
df["prime_age"] = ((df["age"] >= 23) & (df["age"] <= 28)).astype(int)
feats = ["age", "age_squared", "pos_enc", "league_enc", "nat_enc", "foot_enc", "appearances", "goals", "assists", "goals_per_90",
         "assists_per_90", "avg_rating", "pass_accuracy", "dribbles_per_90", "tackles_per_90", "contract_years_left",
         "international", "int_caps", "weeks_injured", "goal_contribution", "contribution_per_90", "prime_age"]

X, y = df[feats], df["market_value_m"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
m = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=42).fit(Xtr, ytr)
pred = m.predict(Xte)
r2, mae = r2_score(yte, pred), mean_absolute_error(yte, pred)
df["pred"] = m.predict(X).round(2)
df["gap"] = (df["pred"] - df["market_value_m"]).round(2)
imp = pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False).head(10)
POS = {"ST": "#f85149", "CAM": "#ff7b72", "LW": "#ffa657", "RW": "#f0883e", "CM": "#d2a8ff", "CDM": "#79c0ff", "CB": "#56d364", "LB": "#3fb950", "RB": "#2ea043", "GK": "#58a6ff"}
LG = ["#E1306C", "#ffa657", "#69C9D0", "#3fb950", "#d2a8ff"]

te = df.loc[Xte.index]
f1 = go.Figure()
for p in POS:
    s = te[te["position"] == p]
    f1.add_trace(go.Scatter(x=s["market_value_m"], y=s["pred"], mode="markers", name=p, marker=dict(color=POS[p], size=7, opacity=0.75),
        text=s["name"], hovertemplate="<b>%{text}</b><br>Actual €%{x:.1f}M<br>Predicted €%{y:.1f}M<extra></extra>"))
lim = max(yte.max(), pred.max()) + 5
f1.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines", line=dict(color="white", dash="dash"), showlegend=False))
f1.update_layout(**{**BASE, "title": f"Actual vs Predicted (R² {r2:.3f}, MAE €{mae:.2f}M)", "xaxis_title": "Actual (€M)", "yaxis_title": "Predicted (€M)", "height": 420})

f2 = go.Figure(go.Bar(x=imp.values[::-1], y=imp.index[::-1], orientation="h", marker_color="#388bfd",
    text=[f"{v:.3f}" for v in imp.values[::-1]], textposition="outside"))
f2.update_layout(**{**BASE, "title": "Top 10 Feature Importances", "height": 420})

pos = df.groupby("position")["market_value_m"].mean().sort_values()
f3 = go.Figure(go.Bar(x=pos.values, y=pos.index, orientation="h", marker_color=[POS[p] for p in pos.index],
    text=[f"€{v:.1f}M" for v in pos.values], textposition="outside"))
f3.update_layout(**{**BASE, "title": "Avg Market Value by Position (€M)"})

f4 = go.Figure()
for i, l in enumerate(df["league"].unique()):
    f4.add_trace(go.Box(y=df[df["league"] == l]["market_value_m"], name=l, marker_color=LG[i]))
f4.update_layout(**{**BASE, "title": "Value Distribution by League (€M)"})

f5 = go.Figure()
for p in POS:
    s = df[df["position"] == p]
    f5.add_trace(go.Scatter(x=s["age"], y=s["market_value_m"], mode="markers", name=p, marker=dict(color=POS[p], size=5, opacity=0.6),
        text=s["name"], hovertemplate="<b>%{text}</b><br>Age %{x}<br>€%{y:.1f}M<extra></extra>"))
ar = np.linspace(df["age"].min(), df["age"].max(), 100)
f5.add_trace(go.Scatter(x=ar, y=np.poly1d(np.polyfit(df["age"], df["market_value_m"], 2))(ar), mode="lines", name="Trend", line=dict(color="white", dash="dash", width=2)))
f5.update_layout(**{**BASE, "title": "Age vs Market Value", "xaxis_title": "Age", "height": 420})

f6 = go.Figure()
for i, l in enumerate(df["league"].unique()):
    s = df[df["league"] == l]
    f6.add_trace(go.Scatter(x=s["goals"], y=s["market_value_m"], mode="markers", name=l, marker=dict(color=LG[i], size=6, opacity=0.65), text=s["name"],
        hovertemplate="<b>%{text}</b><br>Goals %{x}<br>€%{y:.1f}M<extra></extra>"))
f6.update_layout(**{**BASE, "title": "Goals vs Market Value", "xaxis_title": "Goals", "height": 420})

uv = df.sort_values("gap", ascending=False).head(12)
lab = [f"{r['name']}<br>{r['position']} · {r['league'][:3]}" for _, r in uv.iterrows()]
f7 = go.Figure([go.Bar(name="Market Value", x=lab, y=uv["market_value_m"], marker_color="#f85149"),
                go.Bar(name="Model Value", x=lab, y=uv["pred"], marker_color="#3fb950", customdata=uv["gap"],
                       hovertemplate="Model €%{y:.1f}M<br>Gap +€%{customdata:.1f}M<extra></extra>")])
f7.update_layout(**{**BASE, "title": "Top 12 Undervalued Players: Market vs Model (€M)", "barmode": "group", "height": 420})

page("outputs/football_dashboard_interactive.html", "Football Player Value Predictor", "800 players · 5 leagues · Gradient Boosting",
    [("R² Score", f"{r2:.3f}", "Variance explained", "#3fb950"), ("Mean Abs Error", f"€{mae:.2f}M", "Avg prediction error", "#ffa657"),
     ("Top Feature", imp.index[0], f"{imp.values[0]:.1%} importance", "#58a6ff"),
     ("Undervalued", f"{(df['gap'] > 3).sum()}", "Priced below model value", "#f85149")],
    [("Model Performance", ["f1", "f2"]), ("Value Analysis", ["f3", "f4"]), ("Age and Output", ["f5", "f6"]), ("Scouting", ["f7"])],
    dict(f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6, f7=f7))

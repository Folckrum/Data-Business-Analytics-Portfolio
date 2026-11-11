import sys, pandas as pd, plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
sys.path.insert(0, "../../shared")
from dash_template import page, BASE, SURFACE, BORDER, TEXT, MUTED

df = pd.read_csv("data/platform_data.csv")
sc = pd.read_csv("outputs/platform_scorecard.csv")
bud = pd.read_csv("outputs/budget_recommendation.csv")
ct = pd.read_csv("outputs/content_type_analysis.csv")
C = {"Instagram": "#E1306C", "YouTube": "#FF0000", "TikTok": "#69C9D0", "LinkedIn": "#0077B5", "Twitter/X": "#1DA1F2", "Facebook": "#1877F2"}


def bar(d, col, title, fmt, horizontal=False):
    d = d.sort_values(col, ascending=horizontal)
    x, y = (d[col], d["platform"]) if horizontal else (d["platform"], d[col])
    f = go.Figure(go.Bar(x=x, y=y, orientation="h" if horizontal else "v", marker_color=[C[p] for p in d["platform"]],
        text=[fmt.format(v) for v in d[col]], textposition="outside"))
    f.update_layout(**{**BASE, "title": title})
    return f


f1 = bar(sc, "platform_score", "Overall Platform Score (0–10)", "{:.1f}", True)
f2 = bar(sc, "avg_eng_rate", "Avg Engagement Rate (%)", "{:.1f}%")
f3 = bar(sc, "avg_roas", "Avg ROAS", "{:.1f}x")
f3.add_hline(y=1, line_dash="dash", line_color="white", opacity=0.4, annotation_text="Break-even")
f4 = bar(sc, "reach_per_dollar", "Reach per ₹1 Spent", "{:.2f}", True)
f5 = bar(sc, "avg_cpm", "CPM — cost per 1000 impressions (₹)", "₹{:.1f}", True)

f6 = go.Figure()
for p in C:
    s = df[df["platform"] == p].groupby("month", sort=False)["engagement_rate"].mean()
    f6.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", name=p, line=dict(color=C[p], width=2)))
f6.update_layout(**{**BASE, "title": "Monthly Engagement Rate (%)"})

f7 = go.Figure(go.Pie(labels=bud["platform"], values=bud["recommended_budget"], hole=0.45,
    marker=dict(colors=[C[p] for p in bud["platform"]]), textinfo="label+percent"))
f7.update_layout(**{**BASE, "title": "Recommended Budget (₹50,000/mo)", "annotations": [dict(text="₹50K", showarrow=False, font=dict(size=18))]})

cols = ["avg_eng_rate", "total_reach", "avg_roas", "reach_per_dollar", "follower_per_dollar", "platform_score"]
names = ["Engagement", "Reach", "ROAS", "Reach/₹", "Followers/₹", "Score"]
norm = MinMaxScaler().fit_transform(sc[cols])
f8 = go.Figure()
for i, r in sc.iterrows():
    v = list(norm[i]) + [norm[i][0]]
    f8.add_trace(go.Scatterpolar(r=v, theta=names + names[:1], fill="toself", name=r["platform"], opacity=0.6, line=dict(color=C[r["platform"]])))
f8.update_layout(**{**BASE, "title": "Platform Comparison Radar", "height": 420,
    "polar": dict(bgcolor=SURFACE, radialaxis=dict(gridcolor=BORDER, tickfont=dict(color=MUTED)), angularaxis=dict(tickfont=dict(color=TEXT)))})

pv = ct.pivot_table(index="platform", columns="content_type", values="avg_engagement_rate").round(2)
f9 = go.Figure(go.Heatmap(z=pv.values, x=pv.columns.tolist(), y=pv.index.tolist(), colorscale="YlOrRd",
    text=pv.values, texttemplate="%{text}%"))
f9.update_layout(**{**BASE, "title": "Engagement by Content Type (%)", "height": 420, "margin": dict(l=90, r=30, t=50, b=80)})

top, roas, cheap = sc.loc[sc["platform_score"].idxmax()], sc.loc[sc["avg_roas"].idxmax()], sc.loc[sc["avg_cpm"].idxmin()]
page("outputs/platform_dashboard_interactive.html", "Platform Intelligence Report", "Fashion & Lifestyle · 6 platforms · 2024",
    [("Top Platform", top["platform"], f"Score {top['platform_score']:.1f}/10", "#69C9D0"),
     ("Best ROAS", roas["platform"], f"{roas['avg_roas']:.1f}x return", "#3fb950"),
     ("Cheapest Reach", cheap["platform"], f"₹{cheap['avg_cpm']:.1f} CPM", "#ffa657"),
     ("Budget", "₹50,000/mo", f"Split across {len(sc)} platforms", "#e6edf3")],
    [("Scores and Core Metrics", ["f1", "f2"]), ("Return and Efficiency", ["f3", "f4"]), ("Trend", ["f6"]),
     ("Cost and Budget", ["f5", "f7"]), ("Strategy", ["f8", "f9"])],
    dict(f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6, f7=f7, f8=f8, f9=f9))

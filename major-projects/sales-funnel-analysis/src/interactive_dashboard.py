import sys, pandas as pd, plotly.graph_objects as go
sys.path.insert(0, "../../shared")
from dash_template import page, BASE

df = pd.read_csv("data/funnel_data.csv")
funnel = pd.read_csv("outputs/funnel_summary.csv")
channel = pd.read_csv("outputs/channel_breakdown.csv").sort_values("overall_conv_pct", ascending=False)
device = pd.read_csv("outputs/device_breakdown.csv")
monthly = pd.read_csv("outputs/monthly_trend.csv")

stages = ["visit", "product_view", "add_to_cart", "checkout", "purchase"]
labels = ["Visit", "Product View", "Add to Cart", "Checkout", "Purchase"]
CH = {"Organic": "#3fb950", "Paid Ads": "#f85149", "Email": "#388bfd", "Social Media": "#d2a8ff", "Direct": "#ffa657"}
DV = {"Mobile": "#388bfd", "Desktop": "#3fb950", "Tablet": "#ffa657"}

f1 = go.Figure(go.Funnel(y=funnel["stage"], x=funnel["users"], textinfo="value+percent initial",
    marker=dict(color=["#388bfd", "#3fb950", "#ffa657", "#f0883e", "#f85149"])))
f1.update_layout(**{**BASE, "title": "Conversion Funnel", "margin": dict(l=110, r=30, t=50, b=30)})

step = funnel.iloc[1:]
f2 = go.Figure(go.Bar(x=["Visit→View", "View→Cart", "Cart→Checkout", "Checkout→Purchase"], y=step["step_conversion"],
    marker_color=["#3fb950" if v >= 50 else "#ffa657" if v >= 30 else "#f85149" for v in step["step_conversion"]],
    text=[f"{v:.1f}%" for v in step["step_conversion"]], textposition="outside"))
f2.update_layout(**{**BASE, "title": "Step-by-Step Conversion (%)", "yaxis_range": [0, 80]})

f3 = go.Figure(go.Bar(x=channel["channel"], y=channel["overall_conv_pct"], marker_color=[CH[c] for c in channel["channel"]],
    text=[f"{v:.2f}%" for v in channel["overall_conv_pct"]], textposition="outside",
    customdata=channel[["visits", "purchases"]].values,
    hovertemplate="<b>%{x}</b><br>Conv: %{y:.2f}%<br>Visits: %{customdata[0]:,}<br>Purchases: %{customdata[1]:,}<extra></extra>"))
f3.update_layout(**{**BASE, "title": "Conversion Rate by Channel (%)"})

f4 = go.Figure()
for c in CH:
    vals = [df[df["channel"] == c][s].sum() for s in stages]
    f4.add_trace(go.Scatter(x=labels, y=[v / vals[0] * 100 for v in vals], mode="lines+markers", name=c,
        line=dict(color=CH[c], width=3)))
f4.update_layout(**{**BASE, "title": "Funnel Retention by Channel (% of visits, log)", "yaxis_type": "log"})

f5 = go.Figure()
for d in DV:
    f5.add_trace(go.Bar(name=d, x=labels[1:], y=[df[df["device"] == d][s].sum() for s in stages[1:]], marker_color=DV[d]))
f5.update_layout(**{**BASE, "title": "Funnel Volume by Device", "barmode": "group"})

f6 = go.Figure(go.Scatter(x=monthly["month"], y=monthly["conv_pct"], mode="lines+markers", fill="tozeroy",
    line=dict(color="#d2a8ff", width=3), fillcolor="rgba(210,168,255,0.1)"))
f6.add_hline(y=monthly["conv_pct"].mean(), line_dash="dash", line_color="#f85149", annotation_text="avg")
f6.update_layout(**{**BASE, "title": "Monthly Conversion Rate (%)"})

pv = df.groupby(["channel", "device"])["purchase"].mean().unstack() * 100
f7 = go.Figure(go.Heatmap(z=pv.values, x=pv.columns.tolist(), y=pv.index.tolist(), colorscale="YlGnBu",
    text=pv.values.round(2), texttemplate="%{text}%"))
f7.update_layout(**{**BASE, "title": "Conversion: Channel × Device (%)", "margin": dict(l=100, r=30, t=50, b=50)})

v, b = int(funnel.iloc[0]["users"]), int(funnel.iloc[-1]["users"])
best, worst = channel.iloc[0], channel.iloc[-1]
page("outputs/funnel_dashboard_interactive.html", "Sales Funnel Analysis", f"{v:,} sessions · 5 channels · 3 devices",
    [("Total Visits", f"{v:,}", "Jan – Dec 2024", "#e6edf3"), ("Purchases", f"{b:,}", f"{b/v*100:.2f}% overall conversion", "#3fb950"),
     ("Best Channel", best["channel"], f"{best['overall_conv_pct']:.2f}% conversion", "#388bfd"),
     ("Worst Channel", worst["channel"], f"{worst['overall_conv_pct']:.2f}% conversion", "#f85149")],
    [("The Funnel", ["f1", "f2"]), ("Channels", ["f3", "f4"]), ("Device and Time", ["f5", "f6"]), ("Channel × Device", ["f7"])],
    dict(f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6, f7=f7))

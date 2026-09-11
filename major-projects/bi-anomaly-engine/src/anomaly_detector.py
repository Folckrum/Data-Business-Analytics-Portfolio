import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class Anomaly:
    date: str
    metric: str
    segment: str
    method: str
    actual: float
    expected: float
    deviation_pct: float
    severity: str      # critical / warning / info
    direction: str     # spike / drop
    narrative: str


def severity_level(dev_pct):
    a = abs(dev_pct)
    if a >= 40:
        return "critical"
    elif a >= 20:
        return "warning"
    return "info"


def direction(dev_pct):
    return "spike" if dev_pct > 0 else "drop"


# ── Method 1: Z-Score (rolling 30d) ──────────────────────────────────────────
def zscore_check(series: pd.Series, label: str, segment: str, threshold=3.2) -> List[Anomaly]:
    anomalies = []
    for i in range(30, len(series)):
        window = series.iloc[i-30:i]
        mu, sigma = window.mean(), window.std()
        if sigma == 0:
            continue
        val = series.iloc[i]
        z = (val - mu) / sigma
        if abs(z) >= threshold:
            dev = (val - mu) / mu * 100
            anomalies.append(Anomaly(
                date=series.index[i].strftime("%Y-%m-%d") if hasattr(series.index[i], 'strftime') else str(series.index[i]),
                metric=label,
                segment=segment,
                method="Z-Score",
                actual=round(val, 2),
                expected=round(mu, 2),
                deviation_pct=round(dev, 1),
                severity=severity_level(dev),
                direction=direction(dev),
                narrative=""
            ))
    return anomalies


# ── Method 2: IQR Fence ───────────────────────────────────────────────────────
def iqr_check(series: pd.Series, label: str, segment: str) -> List[Anomaly]:
    anomalies = []
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 3.0 * iqr, q3 + 3.0 * iqr
    median = series.median()
    for idx, val in series.items():
        if val < lo or val > hi:
            dev = (val - median) / median * 100
            anomalies.append(Anomaly(
                date=idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
                metric=label,
                segment=segment,
                method="IQR Fence",
                actual=round(val, 2),
                expected=round(median, 2),
                deviation_pct=round(dev, 1),
                severity=severity_level(dev),
                direction=direction(dev),
                narrative=""
            ))
    return anomalies


# ── Method 3: Week-over-Week Deviation ───────────────────────────────────────
def wow_check(series: pd.Series, label: str, segment: str, threshold_pct=40) -> List[Anomaly]:
    anomalies = []
    weekly = series.resample("W").sum()
    for i in range(1, len(weekly)):
        prev = weekly.iloc[i-1]
        curr = weekly.iloc[i]
        if prev == 0:
            continue
        dev = (curr - prev) / prev * 100
        if abs(dev) >= threshold_pct:
            anomalies.append(Anomaly(
                date=str(weekly.index[i].date()),
                metric=label,
                segment=segment,
                method="WoW Change",
                actual=round(curr, 2),
                expected=round(prev, 2),
                deviation_pct=round(dev, 1),
                severity=severity_level(dev),
                direction=direction(dev),
                narrative=""
            ))
    return anomalies


# ── Method 4: Trend Deviation (linear regression baseline) ───────────────────
def trend_check(series: pd.Series, label: str, segment: str, threshold_pct=50) -> List[Anomaly]:
    anomalies = []
    x = np.arange(len(series))
    y = series.values
    if len(y) < 14:
        return []
    # rolling 60d window — fit line, check last point vs predicted
    for i in range(60, len(series)):
        window_x = x[i-60:i]
        window_y = y[i-60:i]
        coeffs = np.polyfit(window_x, window_y, 1)
        predicted = np.polyval(coeffs, x[i])
        if predicted == 0:
            continue
        dev = (y[i] - predicted) / abs(predicted) * 100
        if abs(dev) >= threshold_pct:
            idx = series.index[i]
            anomalies.append(Anomaly(
                date=idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
                metric=label,
                segment=segment,
                method="Trend Deviation",
                actual=round(float(y[i]), 2),
                expected=round(float(predicted), 2),
                deviation_pct=round(dev, 1),
                severity=severity_level(dev),
                direction=direction(dev),
                narrative=""
            ))
    return anomalies


# ── Narrative Generator ───────────────────────────────────────────────────────
TEMPLATES = {
    ("revenue", "drop", "critical"):
        "{segment} revenue crashed {dev}% on {date} (actual ₹{actual:,} vs expected ₹{expected:,}). "
        "Detected via {method}. Investigate pricing changes, stockouts, or competitor activity.",

    ("revenue", "spike", "critical"):
        "{segment} revenue surged {dev}% on {date} (actual ₹{actual:,} vs expected ₹{expected:,}). "
        "Detected via {method}. Likely a promotion or bulk order — verify if sustainable.",

    ("revenue", "drop", "warning"):
        "{segment} revenue declined {dev}% on {date}. "
        "Below expected ₹{expected:,} — monitor for continuation.",

    ("revenue", "spike", "warning"):
        "{segment} revenue up {dev}% on {date}. "
        "Above trend — check if promo-driven or organic.",

    ("orders", "drop", "critical"):
        "Order volume in {segment} fell {dev}% on {date} ({actual:,} vs expected {expected:,}). "
        "Potential checkout issue, payment failure, or demand collapse.",

    ("orders", "spike", "critical"):
        "Order surge in {segment} — {dev}% above normal on {date}. "
        "Check fulfilment capacity and inventory levels immediately.",

    ("returns", "spike", "critical"):
        "Return rate spiked {dev}% in {segment} on {date}. "
        "Likely product quality issue or mislabelled listings. Escalate to ops team.",

    ("returns", "spike", "warning"):
        "Returns elevated {dev}% in {segment}. "
        "Review recent shipment batch for quality issues.",

    ("tickets_opened", "spike", "critical"):
        "Support ticket volume up {dev}% on {date}. "
        "Correlates with product issues or delivery failures. Check escalation queue.",

    ("csat_score", "drop", "critical"):
        "CSAT dropped to {actual} on {date} ({dev}% below baseline). "
        "Customer satisfaction crisis — review recent support interactions.",

    ("conversions", "drop", "critical"):
        "Marketing conversions dropped {dev}% on {date}. "
        "Ad spend may not be reaching the right audience, or landing page issues.",

    ("roas", "drop", "warning"):
        "ROAS fell to {actual} on {date} — below healthy threshold. "
        "Review campaign targeting and bid strategy.",
}


def build_narrative(a: Anomaly) -> str:
    metric_key = a.metric.lower().replace(" ", "_")
    key = (metric_key, a.direction, a.severity)
    template = TEMPLATES.get(key)
    if not template:
        # generic fallback
        template = (
            "{segment} — {metric} {direction} of {dev}% on {date}. "
            "Actual: {actual:,} vs expected {expected:,}. Detected via {method}."
        )
    try:
        return template.format(
            segment=a.segment,
            metric=a.metric,
            direction=a.direction,
            dev=abs(a.deviation_pct),
            date=a.date,
            actual=a.actual,
            expected=a.expected,
            method=a.method,
        )
    except Exception:
        return f"{a.segment} — {a.metric} {a.direction} of {abs(a.deviation_pct)}% on {a.date}."


# ── Main Runner ───────────────────────────────────────────────────────────────
def run_detection(sales: pd.DataFrame, support: pd.DataFrame, marketing: pd.DataFrame) -> List[Anomaly]:
    all_anomalies = []

    # sales — category level (aggregated across regions)
    sales["date"] = pd.to_datetime(sales["date"])
    for cat in sales["category"].unique():
        sub = sales[sales["category"] == cat].groupby("date")[["revenue","orders","returns"]].sum()
        sub = sub.sort_index()
        for metric in ["revenue", "orders", "returns"]:
            s = sub[metric].astype(float)
            all_anomalies += zscore_check(s, metric, cat)
            all_anomalies += wow_check(s, metric, cat)
            all_anomalies += trend_check(s, metric, cat)

    # region level
    for reg in sales["region"].unique():
        sub = sales[sales["region"] == reg].groupby("date")[["revenue","orders"]].sum()
        sub = sub.sort_index()
        for metric in ["revenue", "orders"]:
            s = sub[metric].astype(float)
            all_anomalies += zscore_check(s, metric, f"Region: {reg}")

    # support — daily overall
    support["date"] = pd.to_datetime(support["date"])
    sup = support.set_index("date").sort_index()
    for metric in ["tickets_opened", "csat_score", "escalations"]:
        s = sup[metric].astype(float)
        all_anomalies += zscore_check(s, metric, "Support")
        all_anomalies += iqr_check(s, metric, "Support")

    # marketing
    marketing["date"] = pd.to_datetime(marketing["date"])
    mkt = marketing.set_index("date").sort_index()
    for metric in ["conversions", "roas", "cpc"]:
        s = mkt[metric].astype(float)
        all_anomalies += zscore_check(s, metric, "Marketing")
        all_anomalies += wow_check(s, metric, "Marketing")

    # deduplicate — same date+metric+segment, keep highest severity
    seen = {}
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    for a in all_anomalies:
        k = (a.date, a.metric, a.segment)
        if k not in seen or sev_order[a.severity] < sev_order[seen[k].severity]:
            seen[k] = a

    result = list(seen.values())

    # build narratives
    for a in result:
        a.narrative = build_narrative(a)

    result.sort(key=lambda x: ({"critical": 0, "warning": 1, "info": 2}[x.severity], x.date))
    print(f"anomalies detected: {len(result)} ({sum(1 for a in result if a.severity=='critical')} critical)")
    return result

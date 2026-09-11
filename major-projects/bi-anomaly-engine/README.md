# 🏆 BI Anomaly Engine — Automated Business Intelligence Platform

> Ingests multi-source business data → runs 4 statistical detection methods → auto-generates narrative insights → renders a live dark-mode HTML intelligence report.

---

## What This Does

Most BI tools show you numbers. This system **reads the numbers and tells you what happened** — in plain English, with severity levels, root cause context, and actionable recommendations. Zero manual work after setup.

**Input:** Raw sales, support, and marketing data (CSV + SQLite)
**Output:** A self-contained HTML report that opens in any browser — dark mode dashboard, interactive charts, anomaly tables with narrative commentary, and live search/filter.

---

## Architecture

```
data sources
  ├── sales.csv          (366 days × 5 categories × 4 regions)
  ├── support.csv        (daily ticket, CSAT, escalation metrics)
  └── marketing.csv      (spend, ROAS, CPC, conversions)
          │
          ▼
   data_generator.py     ← synthetic data with 4 injected real anomalies
          │
          ▼
   anomaly_detector.py   ← 4 detection methods run across all metrics/segments
   ┌──────────────────────────────────────┐
   │  Z-Score (rolling 30d window)        │
   │  IQR Fence (global outlier bounds)   │
   │  Week-over-Week % Change             │
   │  Trend Deviation (linear regression) │
   └──────────────────────────────────────┘
          │
          ▼ anomalies deduped + ranked by severity
          │
          ▼
   report_generator.py   ← builds self-contained HTML report
   ┌──────────────────────────────────────┐
   │  KPI strip (WoW change arrows)       │
   │  Daily revenue chart (anomaly dots)  │
   │  Category / Region / Monthly charts  │
   │  Severity donut chart                │
   │  Full anomaly table with narrative   │
   │  Tab filter (All / Critical / Warning│
   │  Live search across all fields       │
   └──────────────────────────────────────┘
          │
          ▼
   reports/bi_report.html
```

---

## Anomalies Injected (for demo)

| # | Anomaly | What to look for |
|---|---|---|
| 1 | Electronics/North revenue crash Dec 20–31 | −68% vs expected — critical |
| 2 | Clothing/South returns spike Oct 10–20 | 45% return rate vs 8% baseline |
| 3 | Sports promo order surge Mar 15–22 | +180% order volume |
| 4 | App channel new customer drop Q2 (Apr–Jun) | −60% acquisitions — mirrors ad spend cut |

---

## Detection Methods

| Method | How it works | Best for |
|---|---|---|
| Z-Score | Rolling 30d mean ± std; flag if \|z\| ≥ 2.5 | Sudden spikes / crashes |
| IQR Fence | Global Q1−2×IQR, Q3+2×IQR bounds | Extreme outliers |
| WoW Change | Week-on-week % diff; flag if \|Δ\| ≥ 25% | Trend reversals |
| Trend Deviation | Rolling 60d linear regression baseline; flag if \|Δ\| ≥ 35% | Gradual drift |

Deduplication: same date+metric+segment keeps only the highest-severity detection.

---

## Narrative Engine

Each anomaly gets a plain-English narrative generated from a template system keyed on `(metric, direction, severity)`:

```
"Electronics / North revenue crashed 68% on 2024-12-23
(actual ₹18,432 vs expected ₹57,600). Detected via Z-Score.
Investigate pricing changes, stockouts, or competitor activity."
```

---

## How to Run

```bash
cd major-projects/bi-anomaly-engine
pip install pandas numpy
python src/run.py
```

Then open `reports/bi_report.html` in any browser.

To regenerate fresh data:
```bash
python src/data_generator.py
python src/run.py
```

---

## Report Features

- Dark mode dashboard (no external CSS dependencies)
- 5 KPI cards with WoW directional arrows
- Daily revenue line chart with red dots marking critical anomaly dates
- Severity donut, category bar, region bar, monthly trend
- Anomaly table with tab filters: All / Critical / Warning
- Live search — filter by segment, metric, date, or keyword
- Fully self-contained HTML — one file, no server needed

---

## Interview Talking Points

> "The interesting part isn't the detection — it's the narrative layer. I mapped every combination of metric + direction + severity to a business-specific insight template, so the output reads like a human analyst wrote it. The detection itself uses 4 methods because no single method catches everything: Z-score is great for spikes, IQR catches extreme outliers, WoW catches trend reversals, and the regression baseline catches slow drift. Together they cover almost anything that can go wrong in a business dataset."

> "The HTML report is fully self-contained — one file you can email, open offline, or host anywhere. All the chart data is embedded as JSON in the page and rendered client-side with Chart.js. The anomaly dots on the revenue chart are the part people notice first — red dots directly on the timeline where something went wrong."

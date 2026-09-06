# 📈 Project 5 — Automated KPI Reporting Dashboard

## Overview
An **automated business KPI reporting pipeline** that computes key business metrics month-over-month and renders a full executive dashboard. In a real job, this script would run on a schedule (cron/Airflow) and email the dashboard to leadership every month-end.

## Business Questions Answered
- How is revenue trending month-over-month?
- Are we acquiring customers faster or slower than last month?
- Is churn going up or down?
- Is our CLTV/CAC ratio healthy (should be 3x+)?
- How satisfied are customers (NPS score trend)?

## KPIs Tracked (6 core metrics)
| KPI | What it measures |
|---|---|
| Revenue | Total monthly revenue with MoM % change |
| New Customers | Acquisition volume vs prior month |
| Avg Order Value | Spend per transaction |
| Churn Rate | % of customers lost (lower = better) |
| NPS Score | Customer satisfaction (0–100 scale) |
| CLTV / CAC Ratio | Lifetime value vs acquisition cost (3x = healthy) |

## Dashboard Panels
1. **KPI Cards** — value + directional arrow (▲/▼) + MoM % change
2. **Monthly Revenue Trend** — line with area fill
3. **New Customer Bar Chart** — monthly acquisition
4. **Churn Rate** — color-coded (red >5%, orange >3%, green ≤3%)
5. **NPS Score Trend** — with 50-point benchmark line
6. **CLTV/CAC Ratio** — with 3x healthy threshold line
7. **Avg Order Value vs Support Tickets** — dual-axis combo chart

## Tools
`Python` · `Pandas` · `Matplotlib` · `GridSpec` · `SQL (Window Functions)`

## How to Run
```bash
cd business-analyst/02_kpi_reporting
python src/kpi_report_generator.py
```

## SQL File
`sql/kpi_queries.sql` contains production-grade queries for:
- Monthly revenue with MoM & YoY growth rates using `LAG()`
- Customer acquisition & churn rates
- Product performance ranking with `RANK()` window function
- NPS score calculation with 3-month rolling average

## Key Findings
- CLTV/CAC ratio dips below 3x in some months → acquisition cost concern
- Churn spikes correlate with months where NPS drops
- Support tickets and avg order value move inversely — higher value orders generate more support load

## Interview Talking Points
> "KPI reporting is the bread and butter of a BA role. I built this as an automated pipeline — the idea is you run it once a month and get a full dashboard out. The CLTV/CAC ratio panel is the most strategic metric here — if that ratio drops below 3x, the business is spending too much to acquire customers relative to what they're worth. I also wrote the SQL version so this could plug directly into a data warehouse."

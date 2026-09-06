# 👥 Project 3 — User Retention Cohort Analysis

## Overview
Cohort analysis tracks how well a business **retains users over time**. Users are grouped by their signup month (cohort), then we measure what % of each cohort is still active in month 1, 2, 3... and so on. This is one of the most important analyses in product and e-commerce.

## Business Questions Answered
- What % of users who signed up in Jan are still buying in month 3?
- Which signup cohort has the best long-term retention?
- Where is the biggest drop-off — month 1 or month 2?
- How much cumulative revenue does each cohort generate?

## Dataset — ~9,000 filtered orders, 3,000 users
| Column | Description |
|---|---|
| user_id | Unique user |
| signup_date | When they first joined |
| order_date | Date of each purchase |
| order_value | Transaction amount |
| cohort_month | Month user signed up (Jan–Jun 2023) |
| months_since_signup | 0 = first month, 1 = next month, etc. |

## Techniques Used
- **Cohort pivot table** — users × months matrix
- **Retention rate** = active users in month N / cohort size × 100
- Heatmap visualization (RdYlGn — red=low, green=high retention)
- Retention curves per cohort
- SQL version with CTEs + window functions (see `/sql/`)

## Tools
`Python` · `Pandas` · `Matplotlib` · `Seaborn` · `SQL (CTEs)`

## How to Run
```bash
cd data-analyst/03_cohort_analysis
python src/cohort_analysis.py
```

## Output Charts
| File | What it shows |
|---|---|
| `01_cohort_retention_heatmap.png` | Full retention matrix — core deliverable |
| `02_retention_curves.png` | Drop-off curves per cohort |
| `03_cohort_sizes.png` | How many users signed up each month |

## Key Findings
- Avg Month-1 retention: ~35–45% (typical for e-commerce)
- Biggest drop-off happens between Month 0 → Month 1
- Later cohorts (May/Jun) show improving retention — product-market fit signal

## Interview Talking Points
> "Cohort analysis is the standard way to measure retention without confusing it with raw active user counts. I built the cohort pivot using Pandas groupby and a period difference calculation, then visualized it as a heatmap — which is exactly how you'd see it in Amplitude or Mixpanel. The SQL version shows I can do the same logic in a data warehouse using CTEs and window functions."

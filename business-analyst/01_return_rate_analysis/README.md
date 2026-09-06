# 📦 Project 4 — E-Commerce Return Rate Root Cause Analysis

## Overview
A Business Analyst project that investigates **why customers return products** and quantifies the revenue impact. The analysis pinpoints which categories, channels, and delivery windows have the highest return rates — giving the business clear action points to reduce losses.

## Business Questions Answered
- What is the overall return rate and how much revenue is lost?
- Which product category has the highest return rate?
- What are the top reasons customers return products?
- Does slower delivery increase return likelihood?
- Which sales channel (Online/Retail/App) has worst return performance?

## Dataset — 5,000 orders, 10 features
| Column | Description |
|---|---|
| category | Electronics / Clothing / Furniture / Books / Toys / Sports |
| channel | Online / Retail / Mobile App |
| return_reason | Defective / Wrong Item / Not as Described / Changed Mind / etc. |
| delivery_days | Days taken to deliver |
| is_returned | 0 = kept, 1 = returned |
| order_value | Revenue at risk per return |

## Techniques Used
- Return rate = returns / total orders × 100 per segment
- Root cause breakdown by reason, category, channel
- Delivery impact analysis — bucketed delivery time vs return rate
- Monthly trend with MoM tracking
- **SQL**: CTEs + window functions for segment ranking and revenue at risk

## Tools
`Python` · `Pandas` · `Matplotlib` · `Seaborn` · `SQL (CTEs, Window Functions)`

## How to Run
```bash
cd business-analyst/01_return_rate_analysis
python src/return_rate_analysis.py
```

## Output
- `outputs/return_rate_dashboard.png` — 6-panel analysis dashboard
- `reports/return_rate_report.txt` — written BA report with recommendations

## Key Findings
- Overall return rate: ~22%
- Electronics has highest return rate — primary reason: Defective
- Orders with 11+ day delivery return at significantly higher rates
- "Not as Described" is a top-3 reason → product listing quality issue

## Recommendations Generated
1. Stricter QC for Electronics category
2. Improve product descriptions to reduce "Not as Described" returns
3. Target delivery SLA below 7 days for high-value orders

## Interview Talking Points
> "This is a classic BA project — you're given return data and asked to find out why. I approached it like a real investigation: start with the overall rate, then break it down by category, reason, channel, and delivery time to find where the problem concentrates. The written report at the end is what a BA actually delivers to stakeholders — not just charts, but insights and recommendations."

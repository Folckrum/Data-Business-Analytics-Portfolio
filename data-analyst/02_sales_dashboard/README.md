# 📊 Project 2 — Sales Performance Dashboard

## Overview
A multi-panel **executive sales dashboard** built entirely in Python. Tracks revenue, profit, regional performance, channel split, and top sales reps for FY 2023 — the kind of dashboard a Data Analyst would build for a business review meeting.

## Business Questions Answered
- What is the total revenue, profit, and avg margin this year?
- Which product category drives the most revenue?
- Which region performs best and worst?
- How is revenue split across Online, Retail, and Wholesale channels?
- Who are the top 10 sales reps by revenue?

## Dataset — 2,000 orders, 12 features
| Column | Description |
|---|---|
| category | Electronics / Clothing / Furniture / Food / Sports |
| region | North / South / East / West / Central |
| channel | Online / Retail Store / Wholesale |
| revenue | units × unit_price × (1 - discount) |
| profit | revenue - cost |
| profit_margin | profit / revenue × 100 |

## Dashboard Panels
1. **KPI Strip** — Revenue, Profit, Units Sold, Avg Margin, Top Region
2. **Monthly Revenue Trend** — line chart with area fill
3. **Revenue by Category** — horizontal bar
4. **Regional Revenue vs Profit** — grouped bar
5. **Channel Split** — pie chart
6. **Quarterly Performance** — Q1–Q4 bar
7. **Top 10 Sales Reps** — leaderboard with margin labels

## Tools
`Python` · `Pandas` · `NumPy` · `Matplotlib` · `GridSpec`

## How to Run
```bash
cd data-analyst/02_sales_dashboard
python src/sales_dashboard.py
```

## Key Findings
- Online channel contributes ~50% of total revenue
- Electronics is the highest revenue category
- Q4 shows peak performance across all regions

## Interview Talking Points
> "This project simulates what a DA would deliver before a quarterly business review — a single-page executive dashboard with KPIs at the top and drill-downs below. I used Matplotlib's GridSpec to precisely control the layout across 7 panels. The KPI strip with MoM arrows is what stakeholders look at first, so I made that the visual anchor."

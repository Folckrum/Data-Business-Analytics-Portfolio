# 📉 Project 6 — Customer Churn Analysis & Prediction

## Overview
Identifies which customers are likely to churn, why they churn, and which segments need immediate retention action. Combines **descriptive analysis** (who is churning) with a **Random Forest model** (who will churn next) — the full BA + data science stack in one project.

## Business Questions Answered
- What is the overall churn rate and which plan has it worst?
- At what tenure point do customers churn most?
- What behavioral signals predict churn (support calls, late payments)?
- Which customers are highest risk right now?

## Dataset — 5,000 customers, 11 features
| Column | Description |
|---|---|
| plan | Basic / Standard / Premium |
| tenure_months | How long they've been a customer |
| monthly_charges | What they pay per month |
| support_calls | Number of support contacts |
| late_payments | Missed or delayed payments |
| complaints_6m | Complaints in last 6 months |
| churned | 0 = active, 1 = churned (target variable) |

## Techniques Used
- Churn rate segmentation by plan, region, tenure bucket
- Boxplot comparison — support calls: churned vs retained
- Random Forest classifier (scikit-learn)
- ROC-AUC evaluation + confusion matrix
- Feature importance ranking
- Rule-based SQL churn scoring (no ML dependency in warehouse)

## Tools
`Python` · `Pandas` · `Matplotlib` · `Seaborn` · `Scikit-learn` · `SQL`

## How to Run
```bash
cd business-analyst/03_churn_analysis
pip install scikit-learn
python src/churn_analysis.py
```

## Output
| File | Description |
|---|---|
| `outputs/01_churn_overview.png` | 6-panel churn breakdown dashboard |
| `outputs/02_model_results.png` | Feature importance, confusion matrix, ROC curve |
| `reports/high_risk_customers.csv` | Top 10% highest churn probability customers |
| `reports/churn_report.txt` | Full BA report with recommendations |

## Model Performance
- Algorithm: Random Forest (100 trees, max_depth=6)
- AUC: ~0.82–0.85
- Key features: support_calls, late_payments, tenure_months

## Key Findings
- Churn is highest in months 0–12 — early tenure is critical
- Basic plan churns at 2× the rate of Premium
- 3+ support calls in 30 days is the strongest single churn signal
- High-risk segment flagged for retention team outreach

## Interview Talking Points
> "This project combines two things a BA does — the analysis side (who is churning and why) and the predictive side (who will churn next). I used Random Forest because it gives you feature importance, which is actually more useful than the prediction itself — it tells you what to fix. The SQL file replicates the same churn scoring logic without any ML, which is what you'd actually deploy in a warehouse for daily reporting."

# 📱 Project 1 — Social Media Performance EDA

## Overview
End-to-end **Exploratory Data Analysis** on 1,200 social media posts across Instagram, Twitter, LinkedIn and Facebook. Goal: uncover what drives engagement and give actionable posting strategy recommendations.

## Business Questions Answered
- Which platform drives the highest engagement rate?
- What post type (Video/Image/Text/Carousel) performs best?
- What is the best day and hour to post?
- How do likes, shares, comments correlate?

## Dataset — 1,200 rows, 11 features
| Column | Description |
|---|---|
| platform | Instagram / Twitter / LinkedIn / Facebook |
| post_type | Video / Image / Text / Carousel |
| reach | Unique accounts reached |
| engagement_rate | (likes+comments+shares) / reach × 100 |

## Tools
`Python` · `Pandas` · `NumPy` · `Matplotlib` · `Seaborn`

## How to Run
```bash
cd data-analyst/01_social_media_eda
python src/eda_analysis.py
```

## Output Charts
| File | What it shows |
|---|---|
| `01_engagement_distribution.png` | Likes/Shares/Comments distributions |
| `02_platform_comparison.png` | Engagement & reach by platform |
| `03_post_type_analysis.png` | Avg engagement per post type |
| `04_day_hour_heatmap.png` | Best time-to-post heatmap |
| `05_correlation_matrix.png` | Metric correlations |

## Key Findings
- Video posts generate **2.3× more engagement** than static images
- **Tuesday 10AM–12PM** is the optimal posting window
- Reach and impressions are strongly correlated (0.85+)
- LinkedIn has highest professional reach but lowest comment rate

## Interview Talking Points
> "I performed EDA on social media data to surface engagement patterns. I used histograms, bar charts, and a day×hour heatmap to answer real business questions — like when to post and what content type works best. The heatmap directly shows the optimal posting window which is a decision every content team needs."

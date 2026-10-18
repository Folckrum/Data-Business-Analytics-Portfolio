# ⚽ Football Player Market Value Predictor

Uses **Gradient Boosting** to predict a football player's transfer market value (€M) based on performance stats, age, league, and position. Identifies undervalued players the model believes are priced below their actual worth.

---

## How It Works

```
Player Stats (goals, assists, rating, age, league...)
        ↓
Feature Engineering (age curve, goal contribution, prime_age flag...)
        ↓
Gradient Boosting Regressor (300 trees, depth=4)
        ↓
Predicted Market Value (€M)
        ↓
Gap Analysis → Undervalued / Overvalued Players
```

---

## How to Run

```bash
cd major-projects/football-player-value
pip install pandas numpy matplotlib scikit-learn
python src/player_value.py
```

---

## Output

### Dashboard

![Football Value Dashboard](outputs/football_value_dashboard.png)

---

### Model Performance

| Metric | Score |
|---|---|
| R² Score | **0.867** |
| Mean Absolute Error | **€3.66M** |
| Cross-Val R² (5-fold) | **0.877 ± 0.016** |

The model explains 86.7% of market value variance. Average prediction is off by €3.66M — acceptable for transfer scouting decisions.

---

### Top Feature Importances

| # | Feature | Importance |
|---|---|---|
| 1 | goal_contribution (goals + assists) | 0.388 |
| 2 | avg_rating | 0.141 |
| 3 | age | 0.098 |
| 4 | league_enc | 0.072 |
| 5 | goals_per_90 | 0.063 |
| 6 | pos_enc | 0.051 |
| 7 | int_caps | 0.038 |

**Goal contribution alone explains 38.8% of a player's value.** League matters more than nationality. Being in prime age (23–28) adds a meaningful premium.

---

### Top 10 Undervalued Players

Players where model predicts significantly higher value than current market price — potential transfer targets.

| Player | Position | League | Age | Goals | Market €M | Model €M | Gap |
|---|---|---|---|---|---|---|---|
| Player_0724 | ST | Premier League | 24 | 19 | 52.10 | 64.63 | **+12.53** |
| Player_0755 | CM | Premier League | 18 | 5 | 26.13 | 37.28 | **+11.15** |
| Player_0747 | LW | Ligue 1 | 30 | 16 | 30.37 | 39.73 | **+9.36** |
| Player_0629 | ST | Ligue 1 | 16 | 24 | 25.54 | 34.74 | **+9.20** |
| Player_0761 | LW | Premier League | 24 | 22 | 51.74 | 60.80 | **+9.06** |
| Player_0491 | CAM | Serie A | 30 | 21 | 41.44 | 50.32 | **+8.88** |
| Player_0745 | CAM | Ligue 1 | 23 | 12 | 30.05 | 37.54 | **+7.49** |
| Player_0784 | ST | Premier League | 18 | 20 | 39.11 | 46.42 | **+7.31** |
| Player_0245 | RW | Bundesliga | 16 | 31 | 28.86 | 35.61 | **+6.75** |
| Player_0645 | RW | Bundesliga | 30 | 19 | 40.25 | 46.94 | **+6.69** |

Total undervalued players flagged: **38** | Overvalued: **10**

---

### Average Market Value by Position

| Position | Avg Value | Avg Goals | Avg Rating | Players |
|---|---|---|---|---|
| ST | €49.46M | 21.3 | 6.89 | 75 |
| CAM | €44.83M | 18.0 | 7.08 | 66 |
| RW | €44.40M | 18.8 | 6.97 | 83 |
| LW | €42.49M | 17.7 | 7.01 | 81 |
| CM | €31.73M | 5.4 | 6.97 | 80 |
| CDM | €26.67M | 5.0 | 7.02 | 79 |
| CB | €24.27M | 4.8 | 6.99 | 89 |
| RB | €22.04M | 5.1 | 6.92 | 82 |
| LB | €20.74M | 4.9 | 6.97 | 89 |
| GK | €18.20M | 4.3 | 7.04 | 76 |

---

### Average Market Value by League

| League | Avg Value | Total Value | Players |
|---|---|---|---|
| Premier League | €38.40M | €5,069M | 132 |
| La Liga | €35.83M | €6,270M | 175 |
| Bundesliga | €32.41M | €5,607M | 173 |
| Serie A | €28.81M | €4,177M | 145 |
| Ligue 1 | €25.80M | €4,515M | 175 |

**Premier League commands a 49% premium over Ligue 1** for the same player profile.

---

## Features Used (22 total)

| Category | Features |
|---|---|
| Bio | age, age_squared, preferred_foot, nationality |
| Performance | goals, assists, goals_per_90, assists_per_90, avg_rating, pass_accuracy, dribbles_per_90, tackles_per_90, appearances |
| Engineered | goal_contribution, contribution_per_90, prime_age (23-28), age_squared |
| Context | position, league, contract_years_left, international, int_caps, weeks_injured |

---

## Tools

`Python` · `Pandas` · `NumPy` · `Scikit-learn` · `Matplotlib`

## Files

```
football-player-value/
├── src/player_value.py               ← full pipeline
├── data/players.csv                  ← 800 player dataset
├── outputs/
│   ├── football_value_dashboard.png  ← 7-panel dashboard
│   ├── undervalued_players.csv       ← scouting targets
│   ├── overvalued_players.csv
│   └── position_summary.csv
└── README.md
```

---

## Interview Talking Points

> "The interesting part isn't the model accuracy — 0.867 R² is decent but expected with Gradient Boosting on structured data. What's useful is the gap analysis: players where the model's predicted value is significantly higher than their listed market value. Those are your scouting targets — statistically undervalued relative to their performance. The top feature being goal contribution at 38.8% confirms what clubs already know, but the model also weights league heavily — the same striker is worth €13M more in the Premier League than in Ligue 1 purely due to league multiplier effects."

> "I also added an age-squared feature to capture the non-linear career curve — value peaks around 25-27 and drops sharply after 30. A linear age feature would miss that."

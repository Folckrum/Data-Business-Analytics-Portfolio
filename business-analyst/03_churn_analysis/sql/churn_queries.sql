-- ============================================================
-- CHURN ANALYSIS — SQL
-- Techniques: CTEs, Window Functions, CASE logic
-- ============================================================

-- 1. FLAG CHURNED CUSTOMERS (no order in last 90 days)
WITH last_order AS (
    SELECT
        customer_id,
        MAX(order_date)                                      AS last_order_date,
        COUNT(DISTINCT order_id)                             AS total_orders,
        SUM(order_value)                                     AS total_spent,
        AVG(order_value)                                     AS avg_order_value,
        DATEDIFF(CURRENT_DATE, MAX(order_date))              AS days_since_last_order
    FROM orders
    GROUP BY customer_id
),
churn_flags AS (
    SELECT
        lo.*,
        c.plan,
        c.region,
        c.signup_date,
        DATEDIFF(CURRENT_DATE, c.signup_date) / 30          AS tenure_months,
        CASE
            WHEN lo.days_since_last_order > 90 THEN 1
            ELSE 0
        END                                                  AS is_churned
    FROM last_order lo
    JOIN customers c ON lo.customer_id = c.customer_id
),

-- 2. CHURN RATE BY SEGMENT
segment_churn AS (
    SELECT
        plan,
        region,
        COUNT(*)                                             AS total_customers,
        SUM(is_churned)                                      AS churned,
        ROUND(SUM(is_churned) * 100.0 / COUNT(*), 2)        AS churn_rate_pct,
        ROUND(AVG(total_spent), 2)                           AS avg_cltv,
        ROUND(AVG(tenure_months), 1)                         AS avg_tenure_months
    FROM churn_flags
    GROUP BY plan, region
),

-- 3. TENURE BUCKETS — where is churn highest
tenure_churn AS (
    SELECT
        CASE
            WHEN tenure_months <= 6   THEN '0-6 months'
            WHEN tenure_months <= 12  THEN '7-12 months'
            WHEN tenure_months <= 24  THEN '13-24 months'
            WHEN tenure_months <= 36  THEN '25-36 months'
            ELSE '36+ months'
        END                                                  AS tenure_bucket,
        COUNT(*)                                             AS customers,
        SUM(is_churned)                                      AS churned,
        ROUND(SUM(is_churned) * 100.0 / COUNT(*), 2)        AS churn_rate_pct
    FROM churn_flags
    GROUP BY tenure_bucket
    ORDER BY MIN(tenure_months)
),

-- 4. MONTHLY CHURN TREND
monthly_churn AS (
    SELECT
        DATE_TRUNC('month', last_order_date)                 AS month,
        COUNT(*)                                             AS customers_at_risk,
        SUM(is_churned)                                      AS churned_count,
        ROUND(SUM(is_churned) * 100.0 / COUNT(*), 2)        AS churn_rate_pct,
        ROUND(AVG(SUM(is_churned) * 100.0 / COUNT(*)) OVER (
            ORDER BY DATE_TRUNC('month', last_order_date)
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2)                                                AS rolling_3m_churn
    FROM churn_flags
    GROUP BY DATE_TRUNC('month', last_order_date)
),

-- 5. HIGH-RISK CUSTOMERS (churn score)
risk_scoring AS (
    SELECT
        cf.customer_id,
        cf.plan,
        cf.region,
        cf.tenure_months,
        cf.days_since_last_order,
        cf.total_orders,
        cf.total_spent,
        sc.support_calls,
        sc.late_payments,
        sc.complaints_6m,
        -- simple rule-based churn score
        ROUND(
            CASE WHEN cf.tenure_months < 12       THEN 0.30 ELSE 0 END +
            CASE WHEN sc.support_calls > 7         THEN 0.25 ELSE 0 END +
            CASE WHEN sc.late_payments > 3         THEN 0.25 ELSE 0 END +
            CASE WHEN cf.plan = 'Basic'            THEN 0.10 ELSE 0 END +
            CASE WHEN sc.complaints_6m > 2         THEN 0.10 ELSE 0 END
        , 2)                                                 AS churn_score,
        CASE
            WHEN churn_score >= 0.6 THEN 'High Risk'
            WHEN churn_score >= 0.3 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END                                                  AS risk_segment
    FROM churn_flags cf
    JOIN customer_support sc ON cf.customer_id = sc.customer_id
)

-- OUTPUT: ranked high-risk customers for retention team
SELECT
    customer_id,
    plan,
    region,
    tenure_months,
    days_since_last_order,
    support_calls,
    late_payments,
    churn_score,
    risk_segment,
    RANK() OVER (ORDER BY churn_score DESC)                  AS risk_rank
FROM risk_scoring
WHERE risk_segment IN ('High Risk', 'Medium Risk')
ORDER BY churn_score DESC;

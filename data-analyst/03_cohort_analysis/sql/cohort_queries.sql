-- ============================================================
-- COHORT ANALYSIS SQL QUERIES
-- Database: PostgreSQL / SQLite compatible
-- ============================================================

-- 1. Base cohort table — assign each user their signup cohort month
WITH user_cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM orders
    GROUP BY user_id
),

-- 2. Order activity per user per month
user_activity AS (
    SELECT
        o.user_id,
        DATE_TRUNC('month', o.order_date) AS activity_month,
        COUNT(o.order_id)                 AS orders_placed,
        SUM(o.order_value)                AS monthly_revenue
    FROM orders o
    GROUP BY o.user_id, DATE_TRUNC('month', o.order_date)
),

-- 3. Join cohort + activity, compute months since signup
cohort_activity AS (
    SELECT
        uc.cohort_month,
        ua.activity_month,
        ua.user_id,
        ua.orders_placed,
        ua.monthly_revenue,
        EXTRACT(YEAR FROM AGE(ua.activity_month, uc.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(ua.activity_month, uc.cohort_month)) AS months_since_signup
    FROM user_cohorts uc
    JOIN user_activity ua USING (user_id)
),

-- 4. Count active users per cohort per month
cohort_size AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT user_id) AS cohort_users
    FROM user_cohorts
    GROUP BY cohort_month
),

-- 5. Retention counts
retention_counts AS (
    SELECT
        ca.cohort_month,
        ca.months_since_signup,
        COUNT(DISTINCT ca.user_id) AS active_users
    FROM cohort_activity ca
    WHERE ca.months_since_signup >= 0
    GROUP BY ca.cohort_month, ca.months_since_signup
)

-- 6. Final retention rate table
SELECT
    rc.cohort_month,
    rc.months_since_signup,
    rc.active_users,
    cs.cohort_users,
    ROUND(rc.active_users::NUMERIC / cs.cohort_users * 100, 2) AS retention_rate_pct
FROM retention_counts rc
JOIN cohort_size cs USING (cohort_month)
ORDER BY rc.cohort_month, rc.months_since_signup;


-- ============================================================
-- BONUS: Revenue Cohort Analysis
-- ============================================================
WITH user_cohorts AS (
    SELECT user_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM orders GROUP BY user_id
),
revenue_by_cohort AS (
    SELECT
        uc.cohort_month,
        EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', o.order_date), uc.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', o.order_date), uc.cohort_month)) AS months_since_signup,
        SUM(o.order_value) AS cohort_revenue
    FROM orders o
    JOIN user_cohorts uc USING (user_id)
    WHERE o.order_date >= uc.cohort_month
    GROUP BY uc.cohort_month, months_since_signup
)
SELECT
    cohort_month,
    months_since_signup,
    ROUND(cohort_revenue::NUMERIC, 2) AS cohort_revenue,
    ROUND(SUM(cohort_revenue) OVER (
        PARTITION BY cohort_month ORDER BY months_since_signup
    )::NUMERIC, 2) AS cumulative_revenue
FROM revenue_by_cohort
ORDER BY cohort_month, months_since_signup;

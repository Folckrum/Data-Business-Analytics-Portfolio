-- ============================================================
-- RETURN RATE ROOT CAUSE ANALYSIS — SQL with CTEs
-- Database: PostgreSQL
-- ============================================================

-- 1. BASE METRICS — total orders and returns per category
WITH base_metrics AS (
    SELECT
        category,
        channel,
        region,
        return_reason,
        delivery_days,
        order_value,
        is_returned,
        DATE_TRUNC('month', order_date) AS order_month,
        CASE
            WHEN delivery_days <= 3  THEN '1-3 days'
            WHEN delivery_days <= 7  THEN '4-7 days'
            WHEN delivery_days <= 10 THEN '8-10 days'
            ELSE '11+ days'
        END AS delivery_bucket
    FROM orders
),

-- 2. CATEGORY RETURN RATES
category_return_rates AS (
    SELECT
        category,
        COUNT(*)                                          AS total_orders,
        SUM(is_returned)                                 AS total_returns,
        ROUND(AVG(is_returned) * 100, 2)                 AS return_rate_pct,
        ROUND(AVG(order_value), 2)                       AS avg_order_value,
        ROUND(SUM(is_returned * order_value), 2)         AS lost_revenue
    FROM base_metrics
    GROUP BY category
),

-- 3. RETURN REASON BREAKDOWN
reason_breakdown AS (
    SELECT
        return_reason,
        category,
        COUNT(*)                                          AS return_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total_returns,
        ROUND(AVG(order_value), 2)                        AS avg_return_value
    FROM base_metrics
    WHERE is_returned = 1 AND return_reason IS NOT NULL
    GROUP BY return_reason, category
),

-- 4. DELIVERY IMPACT ANALYSIS
delivery_impact AS (
    SELECT
        delivery_bucket,
        COUNT(*)                                 AS orders,
        ROUND(AVG(is_returned) * 100, 2)         AS return_rate_pct,
        ROUND(AVG(order_value), 2)               AS avg_order_value
    FROM base_metrics
    GROUP BY delivery_bucket
    ORDER BY
        CASE delivery_bucket
            WHEN '1-3 days'  THEN 1
            WHEN '4-7 days'  THEN 2
            WHEN '8-10 days' THEN 3
            ELSE 4
        END
),

-- 5. CHANNEL PERFORMANCE
channel_performance AS (
    SELECT
        channel,
        COUNT(*)                                 AS total_orders,
        SUM(is_returned)                         AS total_returns,
        ROUND(AVG(is_returned) * 100, 2)         AS return_rate_pct,
        ROUND(SUM(is_returned * order_value), 2) AS revenue_lost
    FROM base_metrics
    GROUP BY channel
),

-- 6. MONTHLY TREND with MOVING AVERAGE
monthly_trend AS (
    SELECT
        order_month,
        COUNT(*)                                  AS total_orders,
        SUM(is_returned)                          AS returns,
        ROUND(AVG(is_returned) * 100, 2)          AS return_rate_pct,
        ROUND(AVG(AVG(is_returned) * 100) OVER (
            ORDER BY order_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2)                                     AS moving_avg_3m
    FROM base_metrics
    GROUP BY order_month
),

-- 7. HIGH RISK ORDERS (candidates for proactive intervention)
high_risk_segments AS (
    SELECT
        category,
        channel,
        delivery_bucket,
        COUNT(*)                         AS segment_orders,
        ROUND(AVG(is_returned) * 100, 2) AS segment_return_rate,
        ROUND(SUM(order_value), 2)        AS segment_revenue
    FROM base_metrics
    GROUP BY category, channel, delivery_bucket
    HAVING AVG(is_returned) > 0.30
)

-- FINAL OUTPUT — Combined summary
SELECT 'Category Return Rates' AS analysis_type, category AS dimension,
       return_rate_pct AS metric, total_orders AS volume
FROM category_return_rates
UNION ALL
SELECT 'Channel Performance', channel, return_rate_pct, total_orders
FROM channel_performance
ORDER BY analysis_type, metric DESC;


-- ============================================================
-- WINDOW FUNCTION: Rank categories by return rate within region
-- ============================================================
SELECT
    region,
    category,
    ROUND(AVG(is_returned) * 100, 2)                          AS return_rate_pct,
    RANK() OVER (
        PARTITION BY region ORDER BY AVG(is_returned) DESC
    )                                                          AS rank_in_region,
    ROUND(SUM(order_value), 2)                                 AS total_revenue,
    ROUND(SUM(is_returned * order_value), 2)                   AS revenue_at_risk
FROM orders
GROUP BY region, category
ORDER BY region, rank_in_region;

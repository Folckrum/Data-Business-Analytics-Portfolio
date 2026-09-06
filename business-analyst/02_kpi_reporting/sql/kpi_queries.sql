-- ============================================================
-- KPI REPORTING SQL QUERIES
-- Advanced CTEs, Window Functions, Business Metrics
-- ============================================================

-- 1. MONTHLY REVENUE METRICS WITH GROWTH RATES
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date)         AS month,
        COUNT(DISTINCT order_id)                 AS total_orders,
        COUNT(DISTINCT customer_id)              AS unique_customers,
        SUM(order_value)                         AS revenue,
        AVG(order_value)                         AS avg_order_value,
        SUM(SUM(order_value)) OVER (
            ORDER BY DATE_TRUNC('month', order_date)
        )                                        AS cumulative_revenue
    FROM orders
    WHERE order_status = 'Completed'
    GROUP BY DATE_TRUNC('month', order_date)
),
revenue_with_growth AS (
    SELECT
        month,
        revenue,
        avg_order_value,
        total_orders,
        cumulative_revenue,
        LAG(revenue) OVER (ORDER BY month)       AS prev_month_revenue,
        ROUND(
            (revenue - LAG(revenue) OVER (ORDER BY month))
            / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2
        )                                        AS mom_growth_pct,
        ROUND(
            (revenue - LAG(revenue, 12) OVER (ORDER BY month))
            / NULLIF(LAG(revenue, 12) OVER (ORDER BY month), 0) * 100, 2
        )                                        AS yoy_growth_pct
    FROM monthly_revenue
)
SELECT * FROM revenue_with_growth ORDER BY month;


-- 2. CUSTOMER ACQUISITION & CHURN KPIs
WITH customer_months AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_date)) AS first_order_month,
        DATE_TRUNC('month', MAX(order_date)) AS last_order_month
    FROM orders
    GROUP BY customer_id
),
monthly_cohort AS (
    SELECT
        first_order_month                       AS month,
        COUNT(customer_id)                      AS new_customers
    FROM customer_months
    GROUP BY first_order_month
),
churned_customers AS (
    SELECT
        DATE_TRUNC('month', last_order_month + INTERVAL '1 month') AS churn_month,
        COUNT(customer_id)                                           AS churned
    FROM customer_months
    WHERE last_order_month < DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
    GROUP BY churn_month
),
active_customers AS (
    SELECT
        DATE_TRUNC('month', order_date)     AS month,
        COUNT(DISTINCT customer_id)          AS active_count
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT
    ac.month,
    ac.active_count,
    COALESCE(mc.new_customers, 0)            AS new_customers,
    COALESCE(cc.churned, 0)                  AS churned_customers,
    ROUND(
        COALESCE(cc.churned, 0)::NUMERIC
        / NULLIF(LAG(ac.active_count) OVER (ORDER BY ac.month), 0) * 100, 2
    )                                        AS churn_rate_pct,
    ROUND(
        mc.new_customers::NUMERIC
        / NULLIF(LAG(ac.active_count) OVER (ORDER BY ac.month), 0) * 100, 2
    )                                        AS new_customer_rate_pct
FROM active_customers ac
LEFT JOIN monthly_cohort mc ON ac.month = mc.month
LEFT JOIN churned_customers cc ON ac.month = cc.churn_month
ORDER BY ac.month;


-- 3. PRODUCT KPIs — Top Products by Revenue & Margin
WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        p.cost_price,
        COUNT(oi.order_id)                         AS units_sold,
        SUM(oi.quantity * oi.unit_price)           AS gross_revenue,
        SUM(oi.quantity * p.cost_price)            AS total_cost,
        SUM(oi.quantity * oi.unit_price)
            - SUM(oi.quantity * p.cost_price)      AS gross_profit
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY p.product_id, p.product_name, p.category, p.cost_price
),
ranked_products AS (
    SELECT
        *,
        ROUND(gross_profit / NULLIF(gross_revenue, 0) * 100, 2)  AS margin_pct,
        RANK() OVER (ORDER BY gross_revenue DESC)                 AS revenue_rank,
        RANK() OVER (ORDER BY gross_profit / NULLIF(gross_revenue, 0) DESC) AS margin_rank,
        RANK() OVER (PARTITION BY category ORDER BY gross_revenue DESC)     AS rank_in_category
    FROM product_revenue
)
SELECT
    product_id, product_name, category,
    units_sold, gross_revenue, gross_profit,
    margin_pct, revenue_rank, margin_rank, rank_in_category
FROM ranked_products
WHERE revenue_rank <= 20
ORDER BY revenue_rank;


-- 4. NPS SCORE CALCULATION
WITH nps_responses AS (
    SELECT
        survey_month,
        customer_id,
        score,
        CASE
            WHEN score >= 9  THEN 'Promoter'
            WHEN score >= 7  THEN 'Passive'
            ELSE                  'Detractor'
        END AS respondent_type
    FROM nps_surveys
),
nps_monthly AS (
    SELECT
        survey_month,
        COUNT(*)                                               AS total_responses,
        SUM(CASE WHEN respondent_type = 'Promoter'  THEN 1 ELSE 0 END) AS promoters,
        SUM(CASE WHEN respondent_type = 'Detractor' THEN 1 ELSE 0 END) AS detractors,
        ROUND(
            (SUM(CASE WHEN respondent_type = 'Promoter'  THEN 1.0 ELSE 0 END)
           - SUM(CASE WHEN respondent_type = 'Detractor' THEN 1.0 ELSE 0 END))
            / COUNT(*) * 100, 1
        )                                                      AS nps_score
    FROM nps_responses
    GROUP BY survey_month
)
SELECT
    survey_month,
    total_responses,
    promoters,
    detractors,
    nps_score,
    AVG(nps_score) OVER (
        ORDER BY survey_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3m_nps
FROM nps_monthly
ORDER BY survey_month;

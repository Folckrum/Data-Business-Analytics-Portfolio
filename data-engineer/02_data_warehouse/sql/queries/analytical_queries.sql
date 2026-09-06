-- ============================================================
-- DATA WAREHOUSE — ADVANCED ANALYTICAL QUERIES
-- Techniques: CTEs, Window Functions, Aggregations
-- ============================================================

-- 1. REVENUE RANKING WITH RUNNING TOTALS
WITH revenue_by_category AS (
    SELECT
        p.category,
        SUM(f.net_revenue)                                        AS category_revenue,
        COUNT(DISTINCT f.order_id)                                AS order_count,
        COUNT(DISTINCT f.customer_sk)                             AS unique_customers,
        ROUND(AVG(f.profit_margin_pct), 2)                       AS avg_margin
    FROM fact_sales f
    JOIN dim_product p ON f.product_sk = p.product_sk
    WHERE f.is_returned = 0 AND f.is_cancelled = 0
    GROUP BY p.category
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY category_revenue DESC)              AS revenue_rank,
        ROUND(
            category_revenue / SUM(category_revenue) OVER () * 100, 2
        )                                                         AS revenue_share_pct,
        SUM(category_revenue) OVER (
            ORDER BY category_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                         AS running_total
    FROM revenue_by_category
)
SELECT * FROM ranked ORDER BY revenue_rank;


-- 2. CUSTOMER LIFETIME VALUE (CLTV) SEGMENTATION
WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.segment,
        g.city,
        g.region,
        MIN(d.full_date)                                          AS first_purchase,
        MAX(d.full_date)                                          AS last_purchase,
        COUNT(DISTINCT f.order_id)                                AS total_orders,
        SUM(f.net_revenue)                                        AS total_spent,
        ROUND(AVG(f.net_revenue), 2)                              AS avg_order_value,
        (MAX(d.full_date) - MIN(d.full_date))                     AS customer_lifespan_days,
        COUNT(DISTINCT DATE_TRUNC('month', d.full_date))          AS active_months
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_sk = c.customer_sk AND c.is_current = TRUE
    JOIN dim_date d ON f.date_key = d.date_key
    LEFT JOIN dim_geography g ON f.geo_sk = g.geo_sk
    WHERE f.is_returned = 0 AND f.is_cancelled = 0
    GROUP BY c.customer_id, c.customer_name, c.segment, g.city, g.region
),
cltv_segments AS (
    SELECT
        *,
        ROUND(total_spent / NULLIF(active_months, 0), 2)         AS avg_monthly_spend,
        NTILE(4) OVER (ORDER BY total_spent DESC)                 AS spend_quartile,
        CASE
            WHEN total_orders >= 10 AND total_spent >= 50000 THEN 'Champion'
            WHEN total_orders >= 5  AND total_spent >= 20000 THEN 'Loyal'
            WHEN total_orders >= 3  AND total_spent >= 5000  THEN 'Potential'
            WHEN last_purchase >= CURRENT_DATE - INTERVAL '90 days' THEN 'New'
            ELSE 'At Risk'
        END                                                       AS rfm_segment
    FROM customer_metrics
)
SELECT
    rfm_segment,
    COUNT(*)                                                      AS customer_count,
    ROUND(AVG(total_spent), 2)                                   AS avg_cltv,
    ROUND(AVG(total_orders), 1)                                  AS avg_orders,
    SUM(total_spent)                                              AS segment_revenue
FROM cltv_segments
GROUP BY rfm_segment
ORDER BY avg_cltv DESC;


-- 3. YEAR-OVER-YEAR GROWTH ANALYSIS
WITH yearly AS (
    SELECT
        d.year,
        p.category,
        SUM(f.net_revenue)                                        AS revenue,
        COUNT(DISTINCT f.order_id)                                AS orders,
        COUNT(DISTINCT f.customer_sk)                             AS customers
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_product p ON f.product_sk = p.product_sk
    WHERE f.is_returned = 0
    GROUP BY d.year, p.category
)
SELECT
    current_yr.year,
    current_yr.category,
    current_yr.revenue                                            AS current_revenue,
    prev_yr.revenue                                              AS prev_revenue,
    ROUND(
        (current_yr.revenue - COALESCE(prev_yr.revenue, 0))
        / NULLIF(prev_yr.revenue, 0) * 100, 2
    )                                                            AS yoy_growth_pct,
    current_yr.orders                                            AS current_orders,
    ROUND(current_yr.revenue / NULLIF(current_yr.orders, 0), 2) AS revenue_per_order
FROM yearly current_yr
LEFT JOIN yearly prev_yr
    ON current_yr.category = prev_yr.category
   AND current_yr.year = prev_yr.year + 1
ORDER BY current_yr.year DESC, current_yr.revenue DESC;


-- 4. ROLLING 3-MONTH AVERAGE REVENUE (Moving Average)
WITH monthly_rev AS (
    SELECT
        d.year,
        d.month_number,
        d.month_name,
        SUM(f.net_revenue) AS monthly_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.is_cancelled = 0
    GROUP BY d.year, d.month_number, d.month_name
)
SELECT
    year,
    month_name,
    monthly_revenue,
    ROUND(AVG(monthly_revenue) OVER (
        ORDER BY year, month_number
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                        AS rolling_3m_avg,
    LAG(monthly_revenue) OVER (ORDER BY year, month_number)     AS prev_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year, month_number))
        / NULLIF(LAG(monthly_revenue) OVER (ORDER BY year, month_number), 0) * 100, 2
    )                                                           AS mom_growth_pct
FROM monthly_rev
ORDER BY year, month_number;


-- 5. GEOGRAPHIC REVENUE HEATMAP DATA
SELECT
    g.region,
    g.state,
    g.city,
    COUNT(DISTINCT f.order_id)                                   AS total_orders,
    COUNT(DISTINCT f.customer_sk)                                AS unique_customers,
    ROUND(SUM(f.net_revenue), 2)                                 AS total_revenue,
    ROUND(AVG(f.net_revenue), 2)                                 AS avg_order_value,
    ROUND(SUM(f.gross_profit), 2)                                AS total_profit,
    RANK() OVER (PARTITION BY g.region ORDER BY SUM(f.net_revenue) DESC) AS rank_in_region,
    ROUND(
        SUM(f.net_revenue) * 100.0 / SUM(SUM(f.net_revenue)) OVER (PARTITION BY g.region), 2
    )                                                            AS pct_of_region_revenue
FROM fact_sales f
JOIN dim_geography g ON f.geo_sk = g.geo_sk
WHERE f.is_cancelled = 0
GROUP BY g.region, g.state, g.city
ORDER BY g.region, total_revenue DESC;

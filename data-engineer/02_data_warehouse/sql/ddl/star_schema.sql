-- ============================================================
-- DATA WAREHOUSE — STAR SCHEMA DDL
-- Design: Retail Analytics DWH
-- Pattern: Kimball Dimensional Modeling
-- Database: PostgreSQL
-- ============================================================

-- ── DIMENSION TABLES ─────────────────────────────────────────

-- Date Dimension (pre-populated for 5 years)
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER       PRIMARY KEY,  -- YYYYMMDD
    full_date       DATE          NOT NULL,
    day_of_week     SMALLINT      NOT NULL,     -- 1=Mon, 7=Sun
    day_name        VARCHAR(10)   NOT NULL,
    day_of_month    SMALLINT      NOT NULL,
    day_of_year     SMALLINT      NOT NULL,
    week_of_year    SMALLINT      NOT NULL,
    month_number    SMALLINT      NOT NULL,
    month_name      VARCHAR(10)   NOT NULL,
    month_abbr      CHAR(3)       NOT NULL,
    quarter         SMALLINT      NOT NULL,
    quarter_name    CHAR(2)       NOT NULL,     -- Q1-Q4
    year            SMALLINT      NOT NULL,
    is_weekend      BOOLEAN       NOT NULL DEFAULT FALSE,
    is_holiday      BOOLEAN       NOT NULL DEFAULT FALSE,
    fiscal_year     SMALLINT,
    fiscal_quarter  SMALLINT
);

-- Customer Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk         SERIAL        PRIMARY KEY,  -- Surrogate Key
    customer_id         VARCHAR(20)   NOT NULL,     -- Natural Key
    customer_name       VARCHAR(100),
    email               VARCHAR(150),
    city                VARCHAR(50),
    state               VARCHAR(50),
    country             VARCHAR(50)   DEFAULT 'India',
    segment             VARCHAR(30),
    signup_date         DATE,
    credit_limit        NUMERIC(12, 2),
    is_active           BOOLEAN       DEFAULT TRUE,
    -- SCD Type 2 tracking
    effective_start     DATE          NOT NULL,
    effective_end       DATE,
    is_current          BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP     DEFAULT NOW(),
    updated_at          TIMESTAMP     DEFAULT NOW()
);

CREATE INDEX idx_dim_customer_id ON dim_customer(customer_id);
CREATE INDEX idx_dim_customer_current ON dim_customer(is_current);

-- Product Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_sk      SERIAL        PRIMARY KEY,
    product_id      VARCHAR(20)   NOT NULL UNIQUE,
    product_name    VARCHAR(200),
    category        VARCHAR(50),
    sub_category    VARCHAR(50),
    brand           VARCHAR(50),
    cost_price      NUMERIC(12, 2),
    list_price      NUMERIC(12, 2),
    margin_pct      NUMERIC(5, 2),
    price_tier      VARCHAR(20),  -- Budget, Mid-range, Premium, Luxury
    is_active       BOOLEAN       DEFAULT TRUE,
    launch_date     DATE,
    created_at      TIMESTAMP     DEFAULT NOW()
);

CREATE INDEX idx_dim_product_category ON dim_product(category);

-- Geography Dimension
CREATE TABLE IF NOT EXISTS dim_geography (
    geo_sk          SERIAL        PRIMARY KEY,
    city            VARCHAR(50)   NOT NULL,
    state           VARCHAR(50)   NOT NULL,
    region          VARCHAR(30)   NOT NULL,  -- North, South, East, West
    country         VARCHAR(50)   DEFAULT 'India',
    zone            VARCHAR(20),             -- Metro, Tier-1, Tier-2
    pin_code        VARCHAR(10),
    latitude        NUMERIC(9, 6),
    longitude       NUMERIC(9, 6)
);

-- Channel Dimension
CREATE TABLE IF NOT EXISTS dim_channel (
    channel_sk      SERIAL        PRIMARY KEY,
    channel_name    VARCHAR(50)   NOT NULL,  -- Online, Retail, Mobile App
    channel_type    VARCHAR(30),             -- Digital, Physical
    is_active       BOOLEAN       DEFAULT TRUE
);

-- ── FACT TABLES ──────────────────────────────────────────────

-- Sales Fact Table (Transactional grain — one row per order line)
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_sk            BIGSERIAL     PRIMARY KEY,
    -- Foreign Keys
    order_id            VARCHAR(20)   NOT NULL,
    order_line_id       VARCHAR(30)   NOT NULL,
    date_key            INTEGER       NOT NULL REFERENCES dim_date(date_key),
    customer_sk         INTEGER       NOT NULL REFERENCES dim_customer(customer_sk),
    product_sk          INTEGER       NOT NULL REFERENCES dim_product(product_sk),
    geo_sk              INTEGER       REFERENCES dim_geography(geo_sk),
    channel_sk          INTEGER       REFERENCES dim_channel(channel_sk),
    -- Degenerate Dimensions
    order_status        VARCHAR(20),
    payment_method      VARCHAR(30),
    warehouse_id        VARCHAR(10),
    -- Measures
    quantity            INTEGER       NOT NULL DEFAULT 0,
    unit_price          NUMERIC(12, 2),
    discount_pct        NUMERIC(5, 2) DEFAULT 0,
    gross_revenue       NUMERIC(14, 2),
    discount_amount     NUMERIC(12, 2),
    net_revenue         NUMERIC(14, 2),
    cost_of_goods       NUMERIC(14, 2),
    gross_profit        NUMERIC(14, 2),
    profit_margin_pct   NUMERIC(6, 2),
    -- Additive flags
    is_returned         SMALLINT      DEFAULT 0,
    is_cancelled        SMALLINT      DEFAULT 0,
    -- Audit
    etl_batch_id        VARCHAR(30),
    inserted_at         TIMESTAMP     DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_fact_sales_date   ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_cust   ON fact_sales(customer_sk);
CREATE INDEX idx_fact_sales_prod   ON fact_sales(product_sk);
CREATE INDEX idx_fact_sales_order  ON fact_sales(order_id);
CREATE INDEX idx_fact_sales_status ON fact_sales(order_status);

-- Monthly Aggregate Fact (Periodic Snapshot)
CREATE TABLE IF NOT EXISTS fact_monthly_sales_agg (
    agg_sk              SERIAL        PRIMARY KEY,
    year                SMALLINT      NOT NULL,
    month               SMALLINT      NOT NULL,
    quarter             SMALLINT      NOT NULL,
    customer_sk         INTEGER       REFERENCES dim_customer(customer_sk),
    product_sk          INTEGER       REFERENCES dim_product(product_sk),
    geo_sk              INTEGER       REFERENCES dim_geography(geo_sk),
    -- Aggregated Measures
    total_orders        INTEGER,
    total_units         INTEGER,
    gross_revenue       NUMERIC(16, 2),
    net_revenue         NUMERIC(16, 2),
    total_profit        NUMERIC(16, 2),
    avg_order_value     NUMERIC(12, 2),
    return_count        INTEGER,
    return_rate_pct     NUMERIC(6, 2),
    -- Audit
    refreshed_at        TIMESTAMP     DEFAULT NOW(),
    UNIQUE (year, month, customer_sk, product_sk, geo_sk)
);

-- ── VIEWS FOR REPORTING ───────────────────────────────────────

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    d.year,
    d.month_name,
    d.quarter_name,
    SUM(f.net_revenue)                                           AS net_revenue,
    SUM(f.gross_profit)                                          AS gross_profit,
    COUNT(DISTINCT f.order_id)                                   AS total_orders,
    COUNT(DISTINCT f.customer_sk)                                AS unique_customers,
    ROUND(AVG(f.net_revenue), 2)                                 AS avg_order_value,
    SUM(SUM(f.net_revenue)) OVER (
        PARTITION BY d.year ORDER BY d.month_number
    )                                                            AS ytd_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.is_returned = 0 AND f.is_cancelled = 0
GROUP BY d.year, d.month_name, d.month_number, d.quarter_name;


CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.category,
    p.product_name,
    p.brand,
    p.price_tier,
    SUM(f.quantity)                                              AS units_sold,
    SUM(f.net_revenue)                                           AS total_revenue,
    SUM(f.gross_profit)                                          AS total_profit,
    ROUND(AVG(f.profit_margin_pct), 2)                          AS avg_margin_pct,
    RANK() OVER (ORDER BY SUM(f.net_revenue) DESC)               AS revenue_rank,
    RANK() OVER (PARTITION BY p.category
                 ORDER BY SUM(f.net_revenue) DESC)               AS rank_in_category
FROM fact_sales f
JOIN dim_product p ON f.product_sk = p.product_sk
WHERE f.is_returned = 0
GROUP BY p.category, p.product_name, p.brand, p.price_tier;

-- =====================================================================
-- VELORA BREWING - BUSINESS QUERIES  (SQLite)
-- Each query starts with a line:  -- Q<number>: title
-- Rule used in revenue queries: ignore Cancelled orders.
-- =====================================================================

-- Q1: How many rows are in the main tables? (sanity check)
SELECT 'Sales_Orders' AS table_name, COUNT(*) AS row_count FROM Sales_Orders
UNION ALL SELECT 'Sales_Order_Lines', COUNT(*) FROM Sales_Order_Lines
UNION ALL SELECT 'Production_Batches', COUNT(*) FROM Production_Batches
UNION ALL SELECT 'Procurement_Orders', COUNT(*) FROM Procurement_Orders;

-- Q2: Total revenue, gross profit and margin % (excluding cancelled orders)
SELECT
    ROUND(SUM(l.net_sales_eur), 0)                              AS net_sales_eur,
    ROUND(SUM(l.gross_profit_eur), 0)                           AS gross_profit_eur,
    ROUND(100.0 * SUM(l.gross_profit_eur) / SUM(l.net_sales_eur), 1) AS gross_margin_pct
FROM Sales_Order_Lines l
JOIN Sales_Orders o ON o.order_id = l.order_id
WHERE o.order_status <> 'Cancelled';

-- Q3: Revenue and margin by product (best first)
SELECT
    p.product_name,
    p.beer_style,
    ROUND(SUM(l.net_sales_eur), 0)    AS net_sales_eur,
    ROUND(100.0 * SUM(l.gross_profit_eur) / SUM(l.net_sales_eur), 1) AS margin_pct
FROM Sales_Order_Lines l
JOIN Sales_Orders   o ON o.order_id   = l.order_id
JOIN Product_Master p ON p.product_id = l.product_id
WHERE o.order_status <> 'Cancelled'
GROUP BY p.product_id, p.product_name, p.beer_style
ORDER BY net_sales_eur DESC;

-- Q4: Yearly revenue and growth vs previous year (window function LAG)
WITH yearly AS (
    SELECT SUBSTR(o.order_date, 1, 4) AS year,
           SUM(l.net_sales_eur)       AS net_sales
    FROM Sales_Order_Lines l
    JOIN Sales_Orders o ON o.order_id = l.order_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY year
)
SELECT year,
       ROUND(net_sales, 0) AS net_sales_eur,
       ROUND(100.0 * (net_sales - LAG(net_sales) OVER (ORDER BY year))
             / LAG(net_sales) OVER (ORDER BY year), 1) AS growth_pct
FROM yearly
ORDER BY year;

-- Q5: Monthly revenue with a 3-month moving average (window function)
WITH monthly AS (
    SELECT SUBSTR(o.order_date, 1, 7) AS month,
           SUM(l.net_sales_eur)       AS net_sales
    FROM Sales_Order_Lines l
    JOIN Sales_Orders o ON o.order_id = l.order_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY month
)
SELECT month,
       ROUND(net_sales, 0) AS net_sales_eur,
       ROUND(AVG(net_sales) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0)
           AS moving_avg_3m
FROM monthly
ORDER BY month;

-- Q6: Revenue by sales channel and share of total
SELECT o.sales_channel,
       ROUND(SUM(l.net_sales_eur), 0) AS net_sales_eur,
       ROUND(100.0 * SUM(l.net_sales_eur) / SUM(SUM(l.net_sales_eur)) OVER (), 1) AS share_pct
FROM Sales_Order_Lines l
JOIN Sales_Orders o ON o.order_id = l.order_id
WHERE o.order_status <> 'Cancelled'
GROUP BY o.sales_channel
ORDER BY net_sales_eur DESC;

-- Q7: Top 10 customers by revenue (CTE)
WITH customer_sales AS (
    SELECT o.customer_id,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(l.net_sales_eur)       AS net_sales
    FROM Sales_Orders o
    JOIN Sales_Order_Lines l ON l.order_id = o.order_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY o.customer_id
)
SELECT c.customer_alias, c.customer_type, c.country,
       cs.orders, ROUND(cs.net_sales, 0) AS net_sales_eur
FROM customer_sales cs
JOIN Customers c ON c.customer_id = cs.customer_id
ORDER BY cs.net_sales DESC
LIMIT 10;

-- Q8: Discount level vs margin (does discounting hurt profit?)
SELECT
    CASE WHEN discount_rate = 0     THEN '0% (none)'
         WHEN discount_rate <= 0.05 THEN '0-5%'
         WHEN discount_rate <= 0.10 THEN '5-10%'
         WHEN discount_rate <= 0.15 THEN '10-15%'
         ELSE '15%+' END AS discount_band,
    COUNT(*) AS lines,
    ROUND(100.0 * SUM(gross_profit_eur) / SUM(net_sales_eur), 1) AS margin_pct
FROM Sales_Order_Lines
GROUP BY discount_band
ORDER BY MIN(discount_rate);

-- Q9: Order status summary (how many cancelled / open / delivered?)
SELECT order_status,
       COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM Sales_Orders
GROUP BY order_status
ORDER BY orders DESC;

-- Q10: Production yield and loss by product
SELECT p.product_name,
       COUNT(*)                               AS batches,
       ROUND(100.0 * AVG(b.yield_rate), 1)    AS avg_yield_pct,
       ROUND(SUM(b.production_loss_litre), 0) AS total_loss_litre
FROM Production_Batches b
JOIN Product_Master p ON p.product_id = b.product_id
GROUP BY p.product_id, p.product_name
ORDER BY avg_yield_pct ASC;

-- Q11: Production performance by line (yield, delays, on-hold)
SELECT production_line,
       COUNT(*) AS batches,
       ROUND(100.0 * AVG(yield_rate), 1) AS avg_yield_pct,
       SUM(CASE WHEN batch_status = 'Delayed' THEN 1 ELSE 0 END) AS delayed,
       SUM(CASE WHEN batch_status = 'On Hold' THEN 1 ELSE 0 END) AS on_hold
FROM Production_Batches
GROUP BY production_line
ORDER BY avg_yield_pct DESC;

-- Q12: QC pass rate by product (join across 3 tables)
SELECT p.product_name,
       COUNT(*) AS tests,
       ROUND(100.0 * SUM(CASE WHEN q.quality_status = 'Pass' THEN 1 ELSE 0 END) / COUNT(*), 1)
           AS pass_rate_pct
FROM Quality_Control q
JOIN Production_Batches b ON b.batch_id   = q.batch_id
JOIN Product_Master     p ON p.product_id = b.product_id
GROUP BY p.product_id, p.product_name
ORDER BY pass_rate_pct ASC;

-- Q13: Supplier on-time rate CALCULATED from procurement data
--      (compare with the stated rate in the Suppliers sheet)
SELECT s.supplier_name, s.country,
       COUNT(*) AS orders,
       ROUND(100.0 * SUM(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS calculated_on_time_pct,
       ROUND(100.0 * s.on_time_delivery_rate, 1)                 AS stated_on_time_pct
FROM Procurement_Orders po
JOIN Suppliers s ON s.supplier_id = po.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.country, s.on_time_delivery_rate
ORDER BY calculated_on_time_pct ASC;

-- Q14: Procurement spend by raw-material category
SELECT m.category,
       COUNT(*) AS orders,
       ROUND(SUM(po.purchase_value_eur), 0) AS spend_eur,
       ROUND(AVG(po.lead_time_days), 1)     AS avg_lead_time_days
FROM Procurement_Orders po
JOIN Raw_Materials m ON m.material_id = po.material_id
GROUP BY m.category
ORDER BY spend_eur DESC;

-- Q15: Current stock level per product (sum of all inventory movements)
SELECT p.product_name,
       SUM(i.quantity_change_units) AS stock_units
FROM Inventory_Movements i
JOIN Product_Master p ON p.product_id = i.product_id
GROUP BY p.product_id, p.product_name
ORDER BY stock_units ASC;

-- Q16: Customer complaint mix (feedback by issue category and sentiment)
SELECT issue_category,
       COUNT(*) AS feedback_count,
       SUM(CASE WHEN sentiment_label = 'Negative' THEN 1 ELSE 0 END) AS negative,
       SUM(CASE WHEN sentiment_label = 'Positive' THEN 1 ELSE 0 END) AS positive
FROM Customer_Feedback
GROUP BY issue_category
ORDER BY feedback_count DESC;

-- Q17: Monthly profit and loss = gross profit minus expenses
WITH gp AS (
    SELECT SUBSTR(o.order_date, 1, 7) AS month, SUM(l.gross_profit_eur) AS gross_profit
    FROM Sales_Order_Lines l
    JOIN Sales_Orders o ON o.order_id = l.order_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY month
),
ex AS (
    SELECT SUBSTR(expense_month, 1, 7) AS month, SUM(amount_eur) AS expenses
    FROM Monthly_Expenses
    GROUP BY month
)
SELECT gp.month,
       ROUND(gp.gross_profit, 0) AS gross_profit_eur,
       ROUND(ex.expenses, 0)     AS expenses_eur,
       ROUND(gp.gross_profit - ex.expenses, 0) AS operating_result_eur
FROM gp JOIN ex ON ex.month = gp.month
ORDER BY gp.month DESC
LIMIT 12;

-- Q18: Marketing campaigns - click-through rate and cost per click
SELECT campaign_name_alias, channel,
       spend_eur,
       ROUND(100.0 * clicks / impressions, 2) AS ctr_pct,
       ROUND(spend_eur * 1.0 / clicks, 2)     AS cost_per_click_eur
FROM Marketing_Campaigns
ORDER BY ctr_pct DESC
LIMIT 10;

-- Q19: Rank products by revenue inside each year (RANK window function)
WITH ys AS (
    SELECT SUBSTR(o.order_date, 1, 4) AS year, p.product_name,
           SUM(l.net_sales_eur) AS net_sales
    FROM Sales_Order_Lines l
    JOIN Sales_Orders o   ON o.order_id = l.order_id
    JOIN Product_Master p ON p.product_id = l.product_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY year, p.product_name
)
SELECT * FROM (
    SELECT year, product_name, ROUND(net_sales, 0) AS net_sales_eur,
           RANK() OVER (PARTITION BY year ORDER BY net_sales DESC) AS rank_in_year
    FROM ys
)
WHERE rank_in_year <= 3
ORDER BY year, rank_in_year;

-- Q20: Equipment downtime and maintenance cost by equipment
SELECT equipment,
       COUNT(*) AS jobs,
       ROUND(SUM(downtime_hours), 1)       AS total_downtime_h,
       ROUND(SUM(maintenance_cost_eur), 0) AS total_cost_eur
FROM Equipment_Maintenance
GROUP BY equipment
ORDER BY total_downtime_h DESC;

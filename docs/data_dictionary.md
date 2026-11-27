# Data Dictionary

_Generated automatically by `python src/generate_docs.py` from the Excel file._

17 tables, 26,588 rows in total. All data is **synthetic** (no real people or companies).

## Tables at a glance

| Table | Rows | Columns | Primary key | What it holds |
|---|---:|---:|---|---|
| [Product_Master](#product_master) | 13 | 12 | `product_id` | The 13 beers Velora sells: style, ABV, costs, prices and target yield. |
| [Raw_Materials](#raw_materials) | 14 | 5 | `material_id` | Ingredients and packaging materials bought from suppliers. |
| [Suppliers](#suppliers) | 20 | 7 | `supplier_id` | The 20 suppliers of raw materials. |
| [Employees](#employees) | 100 | 8 | `employee_id` | Staff list (synthetic aliases, no real people). |
| [Distributors](#distributors) | 35 | 5 | `distributor_id` | Companies that distribute Velora beer to customers. |
| [Customers](#customers) | 600 | 6 | `customer_id` | Customer accounts (bars, hotels, shops...). |
| [Marketing_Campaigns](#marketing_campaigns) | 60 | 8 | `campaign_id` | Marketing campaigns with spend, impressions and clicks. |
| [Production_Batches](#production_batches) | 465 | 11 | `batch_id` | One row per brewing batch: planned vs actual volume, yield, status. |
| [Quality_Control](#quality_control) | 465 | 10 | `qc_test_id` | One quality test per batch (temperature, pH, gravity, ABV, defects). |
| [Procurement_Orders](#procurement_orders) | 1,200 | 11 | `po_id` | Purchase orders to suppliers with expected and actual delivery dates. |
| [Sales_Orders](#sales_orders) | 4,500 | 8 | `order_id` | Order headers: who ordered, when, through which channel, and the status. |
| [Sales_Order_Lines](#sales_order_lines) | 11,278 | 9 | `order_line_id` | Order details: one row per product in an order, with sales and profit. |
| [Inventory_Movements](#inventory_movements) | 6,000 | 8 | `movement_id` | Stock changes (production in, sales out...) by product and warehouse. |
| [Monthly_Expenses](#monthly_expenses) | 414 | 5 | `expense_id` | Monthly operating expenses by category and cost centre. |
| [Customer_Feedback](#customer_feedback) | 500 | 9 | `feedback_id` | Customer reviews, complaints and return requests with text. |
| [Equipment_Maintenance](#equipment_maintenance) | 300 | 7 | `maintenance_id` | Maintenance jobs on brewery equipment, with downtime and cost. |
| [Demand_History](#demand_history) | 624 | 5 | `month + product_id` | Monthly units sold per product with promotion and season. |

## Product_Master

The 13 beers Velora sells: style, ABV, costs, prices and target yield.

Rows: **13** | Primary key: `product_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `product_id` | text | Unique product code (VLR001...) | 0% | unique IDs / values |
| `product_name` | text | Beer name | 0% | unique IDs / values |
| `beer_style` | text | Style of beer | 0% | unique IDs / values |
| `abv_percent` | decimal | Alcohol by volume, % | 0% | 0.5 to 7.2 |
| `unit_variable_cost_eur` | decimal | Variable production cost per unit (EUR) | 0% | 0.45 to 0.6 |
| `wholesale_price_eur` | decimal | Standard price to distributors per unit (EUR) | 0% | 1.25 to 2.05 |
| `suggested_retail_price_eur` | decimal | Recommended shelf price per unit (EUR) | 0% | 2.1 to 3.4 |
| `target_yield_rate` | decimal | Planned share of volume that should survive production (0-1) | 0% | 0.84 to 0.94 |
| `pack_size_litre` | decimal | Litres per unit | 0% | 0.5 to 0.5 |
| `pack_format` | text | Package type | 0% | 500ml bottle |
| `launch_date` | text | Date the product went on sale | 0% | 2023-01-01, 2023-07-01 |
| `status` | text | Active or discontinued | 0% | Active |

## Raw_Materials

Ingredients and packaging materials bought from suppliers.

Rows: **14** | Primary key: `material_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `material_id` | text | Unique material code (RM001...) | 0% | unique IDs / values |
| `material_name` | text | Material name | 0% | unique IDs / values |
| `unit` | text | Unit of measure (kg, litre, unit) | 0% | kg, litre, unit |
| `category` | text | Material group (Malt, Hops, Packaging...) | 0% | Flavouring, Hops, Malt, Packaging, Process, Yeast |
| `standard_unit_cost_eur` | decimal | Standard price per unit (EUR) | 0% | 0.04 to 14.2 |

## Suppliers

The 20 suppliers of raw materials.

Rows: **20** | Primary key: `supplier_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `supplier_id` | text | Unique supplier code (SUP001...) | 0% | unique IDs / values |
| `supplier_name` | text | Supplier name | 0% | unique IDs / values |
| `country` | text | Supplier country | 0% | Austria, Czechia, Germany, Hungary, Italy, Slovenia |
| `main_category` | text | Main type of goods supplied | 0% | Hops, Ingredients, Malt, Packaging, Process supplies, Yeast |
| `average_lead_time_days` | decimal | Stated average delivery time in days | 0% | 2.4 to 17.6 |
| `on_time_delivery_rate` | decimal | STATED share of on-time deliveries (0-1); see known issues | 0% | 0.84 to 0.97 |
| `supplier_status` | text | Approved or Under Review | 0% | Approved, Under Review |

## Employees

Staff list (synthetic aliases, no real people).

Rows: **100** | Primary key: `employee_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `employee_id` | text | Unique employee code | 0% | unique IDs / values |
| `employee_name_alias` | text | Anonymised name | 0% | unique IDs / values |
| `department` | text | Department | 0% | 12 distinct values |
| `job_title` | text | Job title | 0% | 30 distinct values |
| `hire_date` | date | Date hired | 0% | 2019-01-07 to 2025-07-18 |
| `work_location` | text | Work site | 0% | Celje, Koper, Ljubljana, Maribor |
| `monthly_salary_eur` | decimal | Monthly salary (EUR) | 0% | 1930.07 to 5104.42 |
| `employment_status` | text | Active or not | 0% | Active |

## Distributors

Companies that distribute Velora beer to customers.

Rows: **35** | Primary key: `distributor_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `distributor_id` | text | Unique distributor code (DST001...) | 0% | unique IDs / values |
| `distributor_name_alias` | text | Anonymised name | 0% | unique IDs / values |
| `country` | text | Distributor country | 0% | Austria, Croatia, Czechia, Germany, Hungary, Italy, Slovenia |
| `channel_type` | text | Type of distribution (Retail, National...) | 0% | Hospitality, National, Regional, Retail |
| `service_level_score` | decimal | Service quality score (0-1) | 0% | 0.75 to 0.99 |

## Customers

Customer accounts (bars, hotels, shops...).

Rows: **600** | Primary key: `customer_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `customer_id` | text | Unique customer code (CUS0001...) | 0% | unique IDs / values |
| `customer_alias` | text | Anonymised name | 0% | unique IDs / values |
| `customer_type` | text | Bar, Hotel, Restaurant, Retailer or Online Customer | 0% | Bar, Hotel, Online Customer, Restaurant, Retailer |
| `country` | text | Customer country | 0% | Austria, Croatia, Czechia, Germany, Hungary, Italy, Slovenia |
| `first_order_date` | date | STATED first order date; unreliable, see known issues | 0% | 2023-01-06 to 2026-11-01 |
| `account_size` | text | Small, Medium or Large | 0% | Large, Medium, Small |

## Marketing_Campaigns

Marketing campaigns with spend, impressions and clicks.

Rows: **60** | Primary key: `campaign_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `campaign_id` | text | Unique campaign code | 0% | unique IDs / values |
| `campaign_name_alias` | text | Anonymised campaign name | 0% | unique IDs / values |
| `channel` | text | Marketing channel | 0% | Distributor Incentive, Email, Retail Promotion, Search Ads, Social Media, Trade Event |
| `start_date` | date | Campaign start date | 0% | 2023-01-20 to 2026-08-14 |
| `spend_eur` | decimal | Money spent (EUR) | 0% | 2363.98 to 24614.8 |
| `impressions` | integer | Times the ad was shown | 0% | 16438 to 223772 |
| `clicks` | integer | Times the ad was clicked | 0% | 530 to 11929 |
| `featured_product_id` | text | Product promoted (links to Product_Master) | 0% | 13 distinct values |

## Production_Batches

One row per brewing batch: planned vs actual volume, yield, status.

Rows: **465** | Primary key: `batch_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `batch_id` | text | Unique batch code (BAT00001...) | 0% | unique IDs / values |
| `production_date` | date | Date the batch was brewed | 0% | 2023-01-05 to 2026-10-28 |
| `product_id` | text | Beer produced (links to Product_Master) | 0% | 13 distinct values |
| `production_line` | text | Maribor Line A, B or C | 0% | Maribor Line A, Maribor Line B, Maribor Line C |
| `planned_volume_litre` | integer | Planned litres | 0% | 700 to 3187 |
| `actual_volume_litre` | integer | Litres actually produced | 0% | 577 to 3152 |
| `production_loss_litre` | integer | planned - actual litres | 0% | 9 to 604 |
| `yield_rate` | decimal | actual / planned (0-1) | 0% | 0.751 to 0.99 |
| `estimated_batch_cost_eur` | decimal | Estimated cost of the batch (EUR) | 0% | 309.08 to 2085.21 |
| `shift_count` | integer | Number of shifts used (1-4) | 0% | 1 to 4 |
| `batch_status` | text | Completed, Delayed or On Hold | 0% | Completed, Delayed, On Hold |

## Quality_Control

One quality test per batch (temperature, pH, gravity, ABV, defects).

Rows: **465** | Primary key: `qc_test_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `qc_test_id` | text | Unique test code (QCT00001...) | 0% | unique IDs / values |
| `batch_id` | text | Batch tested (links to Production_Batches) | 0% | unique IDs / values |
| `test_date` | date | Date of the test (same as production date) | 0% | 2023-01-05 to 2026-10-28 |
| `temperature_c` | decimal | Temperature in degrees C | 0% | 2 to 7.98 |
| `ph_value` | decimal | Acidity (pH) | 0% | 4.01 to 5.2 |
| `specific_gravity` | decimal | Density of the beer relative to water | 0% | 1.008 to 1.06 |
| `measured_abv_percent` | decimal | Measured alcohol, % | 0% | 0.16 to 7.53 |
| `colour_ebc` | integer | Beer colour (EBC scale) | 0% | 1 to 100 |
| `defect_units` | integer | Number of defective units found | 0% | 7 to 31 |
| `quality_status` | text | Pass, or Review when pH is outside 4.1-5.0 or the measured ABV is more than 0.30 points from the product's declared ABV (matches 99.4% of batches) | 0% | Pass, Review |

## Procurement_Orders

Purchase orders to suppliers with expected and actual delivery dates.

Rows: **1,200** | Primary key: `po_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `po_id` | text | Unique purchase order code (PO00001...) | 0% | unique IDs / values |
| `order_date` | date | Date the order was placed | 0% | 2023-01-01 to 2026-10-21 |
| `supplier_id` | text | Supplier (links to Suppliers) | 0% | 20 distinct values |
| `material_id` | text | Material (links to Raw_Materials) | 0% | 14 distinct values |
| `quantity_ordered` | decimal | Quantity ordered (in the material's unit) | 0% | 106.38 to 11991 |
| `unit_cost_eur` | decimal | Price paid per unit (EUR) | 0% | 0.035 to 17.296 |
| `purchase_value_eur` | decimal | quantity x unit cost (EUR) | 0% | 6.7 to 196604 |
| `expected_delivery_date` | date | Promised delivery date | 0% | 2023-01-05 to 2026-11-05 |
| `actual_delivery_date` | date | Date it actually arrived | 0% | 2023-01-05 to 2026-11-08 |
| `lead_time_days` | integer | actual delivery - order date, in days | 0% | 2 to 25 |
| `po_status` | text | Received or Partially Received | 0% | Partially Received, Received |

## Sales_Orders

Order headers: who ordered, when, through which channel, and the status.

Rows: **4,500** | Primary key: `order_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `order_id` | text | Unique order code (ORD000001...) | 0% | unique IDs / values |
| `order_date` | date | Date of the order | 0% | 2023-01-01 to 2026-10-31 |
| `customer_id` | text | Customer (links to Customers) | 0% | 599 distinct values |
| `distributor_id` | text | Distributor (links to Distributors) | 0% | 35 distinct values |
| `sales_channel` | text | Distributor, Online, Hospitality or Retail | 0% | Distributor, Hospitality, Online, Retail |
| `ship_to_country` | text | Delivery country | 0% | Austria, Croatia, Czechia, Germany, Hungary, Italy, Slovenia |
| `order_status` | text | Delivered, Shipped, Open or Cancelled | 0% | Cancelled, Delivered, Open, Shipped |
| `currency` | text | Always EUR | 0% | EUR |

## Sales_Order_Lines

Order details: one row per product in an order, with sales and profit.

Rows: **11,278** | Primary key: `order_line_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `order_line_id` | text | Unique line code (order id + line number) | 0% | unique IDs / values |
| `order_id` | text | Order (links to Sales_Orders) | 0% | 4500 distinct values |
| `product_id` | text | Product sold (links to Product_Master) | 0% | 13 distinct values |
| `quantity_units` | integer | Units sold | 0% | 1 to 1200 |
| `unit_selling_price_eur` | decimal | Price per unit before discount (rounded to 2 decimals) | 0% | 1.18 to 2.21 |
| `discount_rate` | decimal | Discount given (0-1) | 0% | 0 to 0.18 |
| `net_sales_eur` | decimal | Sales after discount (EUR) | 0% | 1.09 to 2477.27 |
| `estimated_cogs_eur` | decimal | Estimated cost of goods sold (EUR) | 0% | 0.45 to 720 |
| `gross_profit_eur` | decimal | net sales - COGS (EUR) | 0% | 0.59 to 1807.51 |

## Inventory_Movements

Stock changes (production in, sales out...) by product and warehouse.

Rows: **6,000** | Primary key: `movement_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `movement_id` | text | Unique movement code | 0% | unique IDs / values |
| `movement_date` | date | Date of the stock change | 0% | 2023-01-01 to 2026-10-22 |
| `product_id` | text | Product (links to Product_Master) | 0% | 13 distinct values |
| `warehouse` | text | Warehouse name | 0% | Celje Depot, Ljubljana Distribution Hub, Maribor Main Warehouse |
| `movement_type` | text | Kind of movement (production receipt, sales dispatch...) | 0% | Adjustment, Damage, Production Receipt, Sales Dispatch, Transfer |
| `quantity_change_units` | integer | Units added (+) or removed (-) | 0% | -1800 to 1798 |
| `batch_reference` | text | Batch that caused it, if any (empty otherwise) | 79% | 435 distinct values |
| `order_reference` | text | Order that caused it, if any (empty otherwise) | 80% | 1054 distinct values |

## Monthly_Expenses

Monthly operating expenses by category and cost centre.

Rows: **414** | Primary key: `expense_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `expense_id` | text | Unique expense code | 0% | unique IDs / values |
| `expense_month` | date | Month of the expense | 0% | 2023-01-01 to 2026-10-01 |
| `expense_category` | text | Type of cost | 0% | 9 distinct values |
| `amount_eur` | decimal | Amount (EUR) | 0% | 5507.59 to 102289 |
| `cost_centre` | text | Department charged | 0% | Group, Ljubljana, Maribor |

## Customer_Feedback

Customer reviews, complaints and return requests with text.

Rows: **500** | Primary key: `feedback_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `feedback_id` | text | Unique feedback code (FB00001...) | 0% | unique IDs / values |
| `feedback_date` | date | Date received | 0% | 2023-01-01 to 2026-10-21 |
| `customer_id` | text | Customer (links to Customers) | 0% | 327 distinct values |
| `product_id` | text | Product (links to Product_Master) | 0% | 13 distinct values |
| `feedback_type` | text | Complaint, Return Request or Review | 0% | Complaint, Return Request, Review |
| `feedback_text` | text | The customer's comment (12 distinct sentences) | 0% | 12 distinct values |
| `sentiment_label` | text | Positive, Neutral or Negative | 0% | Negative, Neutral, Positive |
| `case_status` | text | Resolved, Open or Escalated | 0% | Escalated, Open, Resolved |
| `issue_category` | text | Packaging, Delivery, Order Accuracy, Product Quality or Customer Service; unreliable, see known issues | 0% | Customer Service, Delivery, Order Accuracy, Packaging, Product Quality |

## Equipment_Maintenance

Maintenance jobs on brewery equipment, with downtime and cost.

Rows: **300** | Primary key: `maintenance_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `maintenance_id` | text | Unique job code | 0% | unique IDs / values |
| `maintenance_date` | date | Date of the job | 0% | 2023-01-06 to 2026-10-21 |
| `equipment` | text | Machine serviced | 0% | Bottling Line, Cooling System, Fermentation Tank, Lab Equipment, Pasteuriser |
| `maintenance_type` | text | Preventive or corrective | 0% | Corrective, Emergency, Preventive |
| `downtime_hours` | integer | Hours the machine was stopped | 0% | 1 to 18 |
| `maintenance_cost_eur` | decimal | Cost of the job (EUR) | 0% | 150.57 to 6495.61 |
| `maintenance_status` | text | Status of the job | 0% | Completed, Delayed, Scheduled |

## Demand_History

Monthly units sold per product with promotion and season.

Rows: **624** | Primary key: `month + product_id`

| Column | Type | Meaning | Missing | Values / range |
|---|---|---|---:|---|
| `month` | date | Month (first day) | 0% | 2023-01-01 to 2026-12-01 |
| `product_id` | text | Product (links to Product_Master) | 0% | 13 distinct values |
| `units_sold` | integer | Units sold in that month | 0% | 1443 to 9422 |
| `promotion_discount_rate` | decimal | Promotion discount that month (0-1) | 0% | 0.05 to 0.22 |
| `season` | text | Season label; inconsistent, see known issues | 0% | Autumn, Spring, Summer, Winter |

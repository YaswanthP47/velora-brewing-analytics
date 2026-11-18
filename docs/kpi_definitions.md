# KPI Definitions

_Formulas come from the `KPI_Glossary` sheet; values are calculated from your data by `python src/generate_docs.py`._

| KPI | Formula | Current value | Better is | Notes |
|---|---|---:|---|---|
| Production yield | `actual_volume_litre / planned_volume_litre` | **88.6%** (average of batches) | Higher | Per batch; target per product is in Product_Master |
| Production loss | `planned_volume_litre - actual_volume_litre` | **105,300 litres** (total) | Lower | |
| Supplier on-time rate | `on-time deliveries / total deliveries` | **42.8%** | Higher | On time = actual delivery <= expected delivery. The Suppliers sheet states 90%, which conflicts; use the calculated value |
| Gross profit | `net_sales_eur - estimated_cogs_eur` | **EUR 4,469,197** | Higher | Cancelled orders excluded |
| Gross margin % | `gross_profit_eur / net_sales_eur` | **66.0%** | Higher | On net sales of EUR 6,774,918, cancelled orders excluded |
| Campaign CTR | `clicks / impressions` | **4.98%** (all campaigns) | Interpret by channel | Compare within one channel only |
| Batch quality review rate | `Review batches / all batches` | **29.7%** (138 of 465) | Lower | |
| Customer complaint rate | `complaints / non-cancelled orders` | **3.9%** (147 of 3,735) | Lower | Denominator chosen by us: non-cancelled orders. Complaints = feedback_type 'Complaint' |
| Demand forecast error | `MAE or RMSE between forecast and actual` | _computed in Step 8_ | Lower | Demand_History holds only actual `units_sold`, no forecast column, so the forecast must come from our own model |
| Inventory movement | `sum(quantity_change_units) by product and warehouse` | 13 of 13 products below zero | n/a | There is no opening stock, so totals are net movements, not stock on hand |

## SQL versions (run against `data/velora.db`)

```sql
-- Production yield (average of batches) and total loss
SELECT ROUND(100*AVG(yield_rate),1) AS yield_pct, SUM(production_loss_litre) AS loss_litre
FROM Production_Batches;

-- Supplier on-time rate
SELECT ROUND(100.0*SUM(actual_delivery_date <= expected_delivery_date)/COUNT(*),1) AS on_time_pct
FROM Procurement_Orders;

-- Gross margin % (cancelled orders excluded)
SELECT ROUND(100.0*SUM(l.gross_profit_eur)/SUM(l.net_sales_eur),1) AS gross_margin_pct
FROM Sales_Order_Lines l JOIN Sales_Orders o ON o.order_id = l.order_id
WHERE o.order_status <> 'Cancelled';

-- Batch quality review rate
SELECT ROUND(100.0*SUM(quality_status='Review')/COUNT(*),1) AS review_rate_pct FROM Quality_Control;
```

## Pandas versions

```python
yield_pct   = production_batches['yield_rate'].mean() * 100
on_time_pct = (po['actual_delivery_date'] <= po['expected_delivery_date']).mean() * 100
gross_margin = lines['gross_profit_eur'].sum() / lines['net_sales_eur'].sum() * 100
review_rate = (qc['quality_status'] == 'Review').mean() * 100
```

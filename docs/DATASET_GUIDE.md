# Supply Delay Alerts: Dataset Guide

## Overview

`data/supply_orders.csv` contains 75,000 synthetic orders and 17 columns, with one single-product order per row. The dataset covers eight business units and 120 fictional products. It contains no real company, customer, or supplier records and is not a statistically calibrated industry benchmark.

The CSV uses UTF-8 encoding, comma delimiters, one header row, ISO dates (`YYYY-MM-DD`), decimal points, and empty fields for nulls. Order dates span `2026-01-05` through `2026-09-11`. The dataset is a historical snapshot dated `2026-09-12`; promised dates may fall after it.

The automation uses each row's `snapshot_date`, not the computer's current date. All rows in the supplied dataset share the same snapshot date.

## Data dictionary

Types below describe field meanings in the source data. They are not a complete set of enforced runtime validations.

| Column | Type | Meaning |
| --- | --- | --- |
| `order_id` | string | Unique order identifier. Each row represents one single-product order. |
| `order_date` | date | Date the order was placed. |
| `business_unit` | string | Destination commercial business unit. Eight possible units. |
| `destination_country` | string | Country served by the business unit. |
| `supplier` | string | Fictional supplier responsible for the product. |
| `product_id` | string | Product identifier. The 120 products have stable names and suppliers. |
| `product_name` | string | Fictional brand, product description, and variant. |
| `product_category` | string | Fragrance, Gift Set, Body Care, or Skin Care. |
| `quantity_ordered` | integer | Original quantity in sellable units, in multiples of 12. A gift set is one sellable unit. |
| `quantity_delivered` | integer | Cumulative units received by the snapshot date. Dispatched units are not yet delivered. |
| `unit_price_eur` | decimal | Synthetic net selling price per unit, excluding tax and freight. All countries use EUR for comparison; larger orders receive volume discounts. |
| `promised_delivery_date` | date | Original commitment for full delivery, not dispatch. Never revised in this dataset. |
| `actual_delivery_date` | nullable date | Date full delivery was completed. Blank for all other statuses, including partial delivery. |
| `status` | string | Fulfillment status at the snapshot, as defined below. |
| `priority` | string | Normal or High. All air orders have High priority. |
| `shipping_mode` | string | Road for European units; Sea or Air for other units. |
| `snapshot_date` | date | Observation date, fixed at `2026-09-12` in the supplied dataset. |

## Business rules

An order is active and overdue when both conditions hold:

1. `status` exactly matches `Pending`, `Shipped`, or `Partially Delivered`.
2. `promised_delivery_date` is earlier than that row's `snapshot_date`.

| Status | Meaning | Eligible if overdue? |
| --- | --- | --- |
| Pending | No units have shipped yet. | Yes |
| Shipped | Dispatched, with no receipt recorded. | Yes |
| Partially Delivered | Some, but not all, units have been received. | Yes |
| Delivered | All units have been received. | No |
| Cancelled | Terminal status with no delivered units in this dataset. | No |

Orders due on or after the snapshot date are excluded. Completed deliveries do not require an open-order alert, even if they arrived late. Partial deliveries remain eligible because units are outstanding. The simulation does not include partial cancellations, returns, or overdeliveries.

`actual_delivery_date` provides historical context only. It does not determine eligibility or the overdue calculation. The automation uses the supplied status without deriving it again from quantities or delivery dates.

## Validation and missing values

- All 17 listed columns must exist. A missing column raises `KeyError`.
- Duplicate `order_id` values raise `ValueError` before any status filtering, including duplicates involving cancelled or delivered orders.
- Only exact active-status matches are retained. Unknown, differently capitalized, or missing statuses are excluded without correction or a validation error.
- After status filtering, `promised_delivery_date` and `snapshot_date` are converted using `pd.to_datetime(..., errors="coerce")`. Missing or unparseable values become `NaT`.
- A row with `NaT` in either comparison date is excluded because its overdue status and delay cannot be determined.
- `order_date` and `actual_delivery_date` are retained without datetime conversion. A missing `actual_delivery_date` does not affect eligibility.

Requiring a column does not require every value in it to be populated. The workflow does not apply a blanket missing-value check or validate every quantity, price, or status-to-quantity relationship.

The source dataset intentionally leaves `actual_delivery_date` blank for orders that have not completed delivery. It was generated without deliberate corruptions or duplicate IDs. Tests introduce invalid and missing values separately to verify handling.

## Report

The automation writes `outputs/overdue_orders.csv`, retaining the input columns in their original order and appending:

| Column | Type | Definition |
| --- | --- | --- |
| `days_overdue` | integer | Calendar-day difference: `snapshot_date - promised_delivery_date`. |

For the supplied schema, the report has 18 columns and one row per qualifying order, with no aggregation or quantity proration. Every retained row has a positive `days_overdue` value. For example, a pending order promised on `2026-09-10` with snapshot `2026-09-12` is two days overdue.

Exports omit the pandas index. No qualifying orders, including a valid header-only input, produces headers only. A completely blank input file raises `pandas.errors.EmptyDataError`. Successful reruns replace the previous report; input-validation failures stop before export. The source CSV is not modified.

## Simulation methodology

A seeded simulation (`20260912`) creates uneven regional order volumes, stable product/supplier relationships, bulk order sizes, volume discounts, longer sea-route lead times, increased recent gift-set demand, a supplier disruption from August, and occasional transport delays. Status derives from the simulated fulfillment timeline at the snapshot. Most completed orders are on time or moderately late, with a smaller long-delay tail.

Order placement and receipt dates follow a Monday-Friday calendar; local public holidays are not modeled. The report calculates calendar days overdue, including weekends.

# Supply Delay Alert Generator: practice dataset

75,000 fictional orders, 17 columns. This is synthetic portfolio data created for this project, not Coty data or a statistically calibrated industry benchmark. No real customer or supplier records are used.

## Start here

Use supply_orders.csv. It is a UTF-8, comma-separated CSV with one header row, ISO dates (YYYY-MM-DD), decimal points and empty fields for nulls. Each row is one single-product order, so order_id is unique. Order dates run from 2026-01-05 to 2026-09-11. The snapshot is 2026-09-12; promises can fall after it.

For reproducible practice, compare promised dates with 2026-09-12, not your computer's current date. Treat this as a static historical snapshot.

## Business rules

An active overdue order has promised_delivery_date earlier than snapshot_date and status Pending, Shipped or Partially Delivered. Cancelled orders must be excluded. An order due on the snapshot date is not yet overdue. A delivered order may have arrived late historically, but it no longer needs an open-order alert. Partially Delivered orders still have an outstanding balance.

Pending means no units have shipped yet. Shipped means dispatched with no receipt recorded. Partially Delivered means some but not all units were received. Delivered means all units were received. Cancelled is a terminal status with no delivered units in this simplified dataset. There are no partial cancellations, returns, or overdeliveries.

## Data dictionary

| Column                 | Type          | Meaning                                                                                                                                                         |
| ---------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| order_id               | string        | Unique order identifier. One row is one single-product order.                                                                                                   |
| order_date             | date          | Date the order was placed.                                                                                                                                      |
| business_unit          | string        | Destination commercial business unit. Eight possible units.                                                                                                     |
| destination_country    | string        | Country served by that business unit.                                                                                                                           |
| supplier               | string        | Fictional supplier responsible for the product.                                                                                                                 |
| product_id             | string        | Product identifier. 120 products with stable names and suppliers.                                                                                               |
| product_name           | string        | Fictional brand, product description and variant.                                                                                                               |
| product_category       | string        | Fragrance, Gift Set, Body Care or Skin Care.                                                                                                                    |
| quantity_ordered       | integer       | Original quantity in individual sellable units, in multiples of 12. A gift set is one sellable unit.                                                            |
| quantity_delivered     | integer       | Cumulative units received by the snapshot date. Shipped units are not yet delivered.                                                                            |
| unit_price_eur         | decimal       | Synthetic net selling price per unit in EUR, excluding tax and freight. Larger orders receive volume discounts. All countries use EUR for comparable reporting. |
| promised_delivery_date | date          | Original committed date for full delivery, not dispatch. Never revised in this dataset.                                                                         |
| actual_delivery_date   | nullable date | Date full delivery was completed. Blank for every other status, including partial delivery.                                                                     |
| status                 | string        | Pending, Shipped, Partially Delivered, Delivered or Cancelled, as of the snapshot date.                                                                         |
| priority               | string        | Normal or High. All air orders have High priority.                                                                                                              |
| shipping_mode          | string        | Road for European units. Sea or Air for other units.                                                                                                            |
| snapshot_date          | date          | Fixed observation date: 2026-09-12.                                                                                                                             |

## How the data was simulated

A seeded simulation (seed 20260912) creates uneven regional order volumes, stable product/supplier relationships, bulk order sizes, volume discounts, longer sea-route lead times, increased recent gift-set demand, a supplier disruption from August, and occasional transport delays. Status is derived from the simulated fulfillment timeline at the snapshot, rather than assigned independently of dates. Most completed orders are on time or only moderately late, with a smaller long-delay tail.

Order placement and receipt dates use a Monday-Friday calendar; local public holidays are not modelled. Blank actual delivery dates are intentional, not data-quality defects. There are no deliberately corrupted records or duplicate IDs in this first version.

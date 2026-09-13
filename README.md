# Supply Delay Alerts

Python automation for identifying overdue supply orders and producing an actionable order-level report for delivery follow-up.

**Status:** In development. CSV loading, required-column checks, duplicate-ID validation, status filtering, and date conversion are being assembled into the workflow below.

## Dataset

The project uses a synthetic dataset designed with 75,000 orders and 17 columns. It contains no real company or customer data.

- Input: `data/supply_orders.csv`
- Snapshot: `2026-09-12`
- Field definitions: [Dataset guide](docs/DATASET_GUIDE.md)

## Business rules

An order qualifies when `promised_delivery_date < snapshot_date` and its status exactly matches `Pending`, `Shipped`, or `Partially Delivered`.

- Delivered and cancelled orders are excluded.
- Orders due on the snapshot date are excluded.
- Unknown or missing statuses do not qualify; values are not inferred or corrected.
- Partial deliveries remain eligible because units are outstanding.
- `actual_delivery_date` records full completion and may be blank for other statuses.

All 17 input columns must exist, and duplicate `order_id` values are rejected before filtering.

## Setup and testing

Place the CSV in `data/`. From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

The project uses pandas and pytest. Processing code lives in `src/supply_delay_alerts.py`; tests live in `tests/`.

## Output contract

The completed workflow will write `outputs/overdue_orders.csv`: one row per qualifying order, all 17 original columns in their original order, and an integer `days_overdue` column appended last.

`days_overdue` is the calendar-day difference between `snapshot_date` and `promised_delivery_date`. No aggregation is performed. The export omits the pandas index; no qualifying orders produces headers only. Generated reports are excluded from version control.

## Author

**Ignacio Spreafico**

[Email](mailto:nachospreafico06@gmail.com) · [LinkedIn](https://www.linkedin.com/in/ignacio-spreafico) · [Portfolio](https://ignaciospreafico.vercel.app)

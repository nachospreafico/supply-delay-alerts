# Supply Delay Alerts

Python automation that turns an order CSV into a report of active overdue deliveries. It validates the input schema and order IDs, applies explicit eligibility rules, and exports one row per order for follow-up.

## Dataset

The project uses 75,000 synthetic orders across 17 columns, eight business units, and 120 products. No real company or customer data is used.

- Input: `data/supply_orders.csv`
- Dataset snapshot: `2026-09-12`
- Field definitions and methodology: [Dataset guide](docs/DATASET_GUIDE.md)

## Business rules

An order qualifies when its status exactly matches `Pending`, `Shipped`, or `Partially Delivered` and `promised_delivery_date < snapshot_date`.

- Delivered, cancelled, unknown, and missing statuses are excluded. Status values are not inferred or corrected.
- Orders due on or after the snapshot date are excluded. Partial deliveries remain eligible while units are outstanding.
- Missing or invalid comparison dates become `NaT`; affected orders are excluded.
- `actual_delivery_date` is preserved as context and is not used in filtering or calculations.

All 17 required columns must exist. Duplicate `order_id` values are rejected before filtering. The workflow uses each row's snapshot date, not today's date.

## Setup and usage

Place the dataset at `data/supply_orders.csv`. From the repository root:

```bash
python -m pip install -r requirements.txt
python src/supply_delay_alerts.py
```

The script resolves default paths relative to the project using `pathlib.Path` and creates the output directory if needed. To use custom paths from Python:

```python
from pathlib import Path
from src.supply_delay_alerts import supply_delay_alerts

report = supply_delay_alerts(
    Path("data/supply_orders.csv"),
    Path("outputs/overdue_orders.csv"),
)
```

The function saves the report and returns the resulting DataFrame.

## Output

`outputs/overdue_orders.csv` retains the original columns and appends integer `days_overdue`, calculated as `snapshot_date - promised_delivery_date` in calendar days. The supplied schema produces 18 columns. No aggregation is performed.

Exports omit the pandas index and preserve qualifying row order. No eligible orders, including a valid header-only input, produces headers only. Successful reruns replace the existing report; the input CSV is unchanged. Generated reports are excluded from Git.

Missing or inaccessible files, missing required columns, duplicate IDs, and completely blank files stop processing before export.

## Tests

```bash
python -m pytest -v
```

The pytest suite covers input errors, required columns, duplicate IDs, status and date boundaries, missing or invalid comparison dates, calendar-day calculations, empty reports, output structure, and reruns. Tests use temporary paths; permission failures are simulated without changing real file permissions.

## Author

**Ignacio Spreafico**

[Email](mailto:nachospreafico06@gmail.com) · [LinkedIn](https://www.linkedin.com/in/ignacio-spreafico) · [Portfolio](https://ignaciospreafico.vercel.app)

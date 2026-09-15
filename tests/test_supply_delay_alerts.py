import pytest
import pandas as pd
from src.supply_delay_alerts import supply_delay_alerts

from unittest.mock import patch

import pandas as pd
import pytest

from src.supply_delay_alerts import supply_delay_alerts


@pytest.fixture
def sample_orders():
    return pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 8)],
        "order_date": ["2026-09-01"] * 7,
        "business_unit": ["IBERIA"] * 7,
        "destination_country": ["Spain"] * 7,
        "supplier": ["Sample Supplier"] * 7,
        "product_id": ["PRD-001"] * 7,
        "product_name": ["Sample Gift Set"] * 7,
        "product_category": ["Gift Set"] * 7,
        "quantity_ordered": [100] * 7,
        "quantity_delivered": [0, 0, 0, 0, 40, 100, 0],
        "unit_price_eur": [25.0] * 7,
        "promised_delivery_date": [
            "2026-09-11",  # Pending: overdue by 1 day.
            "2026-09-12",  # Due on snapshot date: exclude.
            "2026-09-13",  # Future delivery: exclude.
            "2026-09-10",  # Shipped: overdue by 2 days.
            "2026-09-10",  # Partially delivered: overdue by 2 days.
            "2026-09-10",  # Delivered: exclude.
            "2026-09-10",  # Cancelled: exclude.
        ],
        "actual_delivery_date": [
            None, None, None, None, None, "2026-09-10", None,
        ],
        "status": [
            "Pending", "Pending", "Pending", "Shipped",
            "Partially Delivered", "Delivered", "Cancelled",
        ],
        "priority": ["Normal"] * 7,
        "shipping_mode": ["Road"] * 7,
        "snapshot_date": ["2026-09-12"] * 7,
    })


def test_missing_file_raises_file_not_found_error(tmp_path):
    output_path = tmp_path / "report.csv"

    with pytest.raises(FileNotFoundError) as exc_info:
        supply_delay_alerts(tmp_path / "missing.csv", output_path)

    assert str(exc_info.value) == (
        "File was not found, please check path to file and if file is present."
    )
    assert not output_path.exists()


def test_inaccessible_file_raises_permission_error(tmp_path):
    output_path = tmp_path / "report.csv"

    # Simulate denied access without depending on OS permissions or real files.
    with patch(
        "src.supply_delay_alerts.pd.read_csv",
        side_effect=PermissionError("Access denied"),
    ):
        with pytest.raises(PermissionError) as exc_info:
            supply_delay_alerts(tmp_path / "orders.csv", output_path)

    assert str(exc_info.value) == (
        "File might be open on another application or user "
        "doesn't have permissions to access it."
    )
    assert not output_path.exists()


@pytest.mark.parametrize("missing_column", [
    "order_id", "order_date", "business_unit", "destination_country",
    "supplier", "product_id", "product_name", "product_category",
    "quantity_ordered", "quantity_delivered", "unit_price_eur",
    "promised_delivery_date", "actual_delivery_date", "status",
    "priority", "shipping_mode", "snapshot_date",
])
def test_missing_column_raises_key_error(sample_orders, tmp_path, missing_column):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "report.csv"
    df = sample_orders.drop(columns=[missing_column])
    df.to_csv(input_path, index=False)

    with pytest.raises(KeyError) as exc_info:
        supply_delay_alerts(input_path, output_path)

    assert exc_info.value.args[0] == "Missing required columns"
    assert not output_path.exists()


def test_duplicate_ids_are_rejected_before_status_filtering(sample_orders, tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "report.csv"
    df = sample_orders.copy()
    # The same ID appears in a pending order and a cancelled order.
    df.loc[6, "order_id"] = df.loc[0, "order_id"]
    df.to_csv(input_path, index=False)

    with pytest.raises(ValueError) as exc_info:
        supply_delay_alerts(input_path, output_path)

    assert str(exc_info.value) == (
        "Duplicated values in order_id, this is not allowed."
    )
    assert not output_path.exists()


def test_exports_active_overdue_orders(sample_orders, tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "outputs" / "report.csv"
    sample_orders.to_csv(input_path, index=False)
    original_input = input_path.read_bytes()

    result = supply_delay_alerts(input_path, output_path)

    assert result["order_id"].tolist() == ["ORD-001", "ORD-004", "ORD-005"]
    assert result["days_overdue"].tolist() == [1, 2, 2]
    assert pd.api.types.is_integer_dtype(result["days_overdue"])
    assert result.columns.tolist() == [*sample_orders.columns, "days_overdue"]

    assert output_path.is_file()
    exported = pd.read_csv(output_path)
    # Compare every exported column, including passthrough values and row order.
    expected = sample_orders.iloc[[0, 3, 4]].reset_index(drop=True).copy()
    expected["days_overdue"] = [1, 2, 2]
    expected["actual_delivery_date"] = float("nan")
    pd.testing.assert_frame_equal(exported, expected)
    assert input_path.read_bytes() == original_input


@pytest.mark.parametrize("status", ["Unknown", "pending", None])
def test_unrecognized_or_missing_status_is_excluded(sample_orders, tmp_path, status):
    input_path = tmp_path / "orders.csv"
    df = sample_orders.copy()
    df.loc[0, "status"] = status
    df.to_csv(input_path, index=False)

    result = supply_delay_alerts(input_path, tmp_path / "report.csv")

    assert result["order_id"].tolist() == ["ORD-004", "ORD-005"]


@pytest.mark.parametrize("column", ["promised_delivery_date", "snapshot_date"])
@pytest.mark.parametrize("value", [None, "not-a-date"])
def test_missing_or_invalid_comparison_date_excludes_order(
    sample_orders, tmp_path, column, value
):
    input_path = tmp_path / "orders.csv"
    df = sample_orders.copy()
    df.loc[0, column] = value
    df.to_csv(input_path, index=False)

    result = supply_delay_alerts(input_path, tmp_path / "report.csv")

    assert result["order_id"].tolist() == ["ORD-004", "ORD-005"]
    assert result["days_overdue"].tolist() == [2, 2]


def test_delay_uses_each_rows_snapshot_across_month_boundary(sample_orders, tmp_path):
    input_path = tmp_path / "orders.csv"
    df = sample_orders.copy()
    df.loc[0, "order_date"] = "2026-08-01"
    df.loc[0, "promised_delivery_date"] = "2026-08-31"
    df.loc[0, "snapshot_date"] = "2026-09-02"
    df.to_csv(input_path, index=False)

    result = supply_delay_alerts(input_path, tmp_path / "report.csv")

    assert result["order_id"].tolist() == ["ORD-001", "ORD-004", "ORD-005"]
    assert result["days_overdue"].tolist() == [2, 2, 2]


@pytest.mark.parametrize("input_kind", ["no_overdue_orders", "headers_only"])
def test_empty_result_exports_headers(sample_orders, tmp_path, input_kind):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "outputs" / "report.csv"
    if input_kind == "headers_only":
        df = sample_orders.iloc[:0].copy()
    else:
        # All three rows are already ineligible under the business rules.
        df = sample_orders.iloc[[1, 2, 5]].copy()
    df.to_csv(input_path, index=False)

    result = supply_delay_alerts(input_path, output_path)

    expected_columns = [*sample_orders.columns, "days_overdue"]
    assert result.empty
    assert result.columns.tolist() == expected_columns
    exported = pd.read_csv(output_path)
    assert exported.empty
    assert exported.columns.tolist() == expected_columns


def test_completely_blank_input_raises_empty_data_error(tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "report.csv"
    input_path.write_text("", encoding="utf-8")

    with pytest.raises(pd.errors.EmptyDataError):
        supply_delay_alerts(input_path, output_path)

    assert not output_path.exists()


def test_successful_rerun_replaces_report(sample_orders, tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "report.csv"
    sample_orders.to_csv(input_path, index=False)
    supply_delay_alerts(input_path, output_path)
    first_report = output_path.read_bytes()

    # Identical input produces an identical report.
    supply_delay_alerts(input_path, output_path)
    assert output_path.read_bytes() == first_report

    # A subsequent empty result replaces the previous data with headers only.
    sample_orders.iloc[:0].to_csv(input_path, index=False)
    supply_delay_alerts(input_path, output_path)
    assert pd.read_csv(output_path).empty


def test_invalid_input_preserves_existing_report(sample_orders, tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "report.csv"
    sample_orders.to_csv(input_path, index=False)
    supply_delay_alerts(input_path, output_path)
    original_report = output_path.read_bytes()

    sample_orders.drop(columns=["order_id"]).to_csv(input_path, index=False)
    with pytest.raises(KeyError):
        supply_delay_alerts(input_path, output_path)

    assert output_path.read_bytes() == original_report

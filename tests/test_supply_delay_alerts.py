import pytest
import pandas as pd
from src.supply_delay_alerts import supply_delay_alerts

supply_orders_path = "./data/supply_orders.csv"

@pytest.fixture
def sample_orders():
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 8)],
        "order_date": ["2026-09-01"] * 7,
        "business_unit": ["IBERIA"] * 7,
        "destination_country": ["Spain"] * 7,
        "supplier": ["Sample Supplier"] * 7,
        "product_id": ["PRD-001"] * 7,
        "product_name": ["Sample Gift Set"] * 7,
        "product_category": ["Gift Sets"] * 7,
        "quantity_ordered": [100] * 7,
        "quantity_delivered": [0, 0, 0, 0, 40, 100, 0],
        "unit_price_eur": [25.0] * 7,
        "promised_delivery_date": [
            "2026-09-11",  # Overdue: 1 day
            "2026-09-12",  # Due on reference date: exclude
            "2026-09-13",  # Future delivery: exclude
            "2026-09-10",  # Overdue: 2 days
            "2026-09-10",  # Partially delivered, overdue: 2 days
            "2026-09-10",  # Delivered: exclude
            "2026-09-10",  # Cancelled: exclude
        ],
        "actual_delivery_date": [
            None, None, None, None,
            "2026-09-09", "2026-09-10", None,
        ],
        "status": [
            "Pending",
            "Pending",
            "Pending",
            "Shipped",
            "Partially Delivered",
            "Delivered",
            "Cancelled",
        ],
        "priority": ["Standard"] * 7,
        "shipping_mode": ["Road"] * 7,
        "snapshot_date": ["2026-09-12"] * 7,
    })

    return df

def test_supply_delay_alerts_raises_file_not_found_error_when_input_is_not_found():
    with pytest.raises(FileNotFoundError) as exc_info:
        supply_delay_alerts("")
    assert str(exc_info.value) == "File was not found, please check path to file and if file is present."

def test_supply_delay_alerts_raises_permission_error_when_input_is_not_accessible():
    with pytest.raises(PermissionError) as exc_info:
        supply_delay_alerts(supply_orders_path)
    assert str(exc_info.value) == "ile might be open on another application or user doesn't have permissions to access it."

def test_supply_delay_alerts_raises_key_error_when_missing_columns(
    sample_orders, tmp_path
):
    file_path = tmp_path / "supply_orders.csv"
    temp_df = sample_orders.drop(columns=["order_id"])
    temp_df.to_csv(file_path, index=False)
    with pytest.raises(KeyError) as exc_info:
        supply_delay_alerts(file_path)
    assert exc_info.value.args[0] == "Missing required columns"

def test_supply_delay_alerts_raises_value_error_when_duplicated_order_id(
    sample_orders, tmp_path
):
    file_path = tmp_path / "supply_orders.csv"
    temp_df = sample_orders
    temp_df["order_id"] = ["ORD-2026-000001"] * 7
    temp_df.to_csv(file_path, index=False)
    with pytest.raises(ValueError) as exc_info:
        supply_delay_alerts(file_path)
    assert str(exc_info.value) == "Duplicated values in order_id, this is not allowed."


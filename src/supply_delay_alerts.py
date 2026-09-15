import pandas as pd
import numpy as np
from pathlib import Path

supply_orders_path = "./data/supply_orders.csv"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "supply_orders.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "overdue_orders.csv"


def supply_delay_alerts(file_path, output_path=OUTPUT_PATH):
    df = load_csv(Path(file_path))
    check_for_required_columns(df)
    check_for_duplicated_values_on_order_id(df)
    df = filter_active_orders(df)
    df = convert_dates_to_datetime(df)
    df = add_days_overdue_column(df)
    save_report(df, output_path)
    return df

def save_report(df, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError as e:
        raise FileNotFoundError("File was not found, please check path to file and if file is present.") from e
    except PermissionError as e:
        raise PermissionError("File might be open on another application or user doesn't have permissions to access it.") from e
    return df

def check_for_required_columns(df):
    required_columns = [
            "order_id",
            "order_date",
            "business_unit",
            "destination_country",
            "supplier",
            "product_id",
            "product_name",
            "product_category",
            "quantity_ordered",
            "quantity_delivered",
            "unit_price_eur",
            "promised_delivery_date",
            "actual_delivery_date",
            "status",
            "priority",
            "shipping_mode",
            "snapshot_date",
        ]
    missing_cols = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_cols:
        raise KeyError("Missing required columns")

def check_for_duplicated_values_on_order_id(df):
    if df["order_id"].duplicated().any():
        raise ValueError("Duplicated values in order_id, this is not allowed.")

def filter_active_orders(df):
    active_statuses = ["Pending", "Shipped", "Partially Delivered"]
    filtered_df = df[df["status"].isin(active_statuses)].copy()
    return filtered_df

def convert_dates_to_datetime(df):
    date_cols = [
            "promised_delivery_date",
            "snapshot_date"
        ]
    for date_col in date_cols:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df

def add_days_overdue_column(df):
    df = df[
        df["promised_delivery_date"] < df["snapshot_date"]
    ].copy()
    df["days_overdue"] = (
        df["snapshot_date"] - df["promised_delivery_date"]
    ).dt.days
    return df

if __name__ == "__main__":
    result = supply_delay_alerts(INPUT_PATH)
    print(f"Saved {len(result)} overdue orders to {OUTPUT_PATH}")
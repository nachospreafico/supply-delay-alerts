import pandas as pd
from pathlib import Path

supply_orders_path = "./data/supply_orders.csv"

def supply_delay_alerts(file_path):
    df = load_csv(file_path)
    check_for_required_columns(df)
    check_for_duplicated_values_on_order_id(df)
    df = filter_df(df)
    date_cols = [
        "promised_delivery_date",
        "actual_delivery_date",
        "snapshot_date"
    ]
    df = convert_dates_to_datetime(df, date_cols)
    check_dates_are_datetime(df, date_cols)


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

def filter_df(df):
    active_statuses = ["Pending", "Shipped", "Partially Delivered"]
    filtered_df = df[df["status"].isin(active_statuses)].copy()
    return filtered_df

def convert_dates_to_datetime(df, date_cols):
    for date_col in date_cols:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


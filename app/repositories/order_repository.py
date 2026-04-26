from __future__ import annotations

import csv
from pathlib import Path

from app.schemas.domain import Order
from app.utils.parsers import get_row_value, parse_date, parse_float


class OrderRepository:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self._orders = self._load_orders()

    def _load_orders(self) -> dict[str, Order]:
        orders: dict[str, Order] = {}
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                order = Order(
                    order_id=str(get_row_value(row, "order_id", "id") or ""),
                    order_date=parse_date(get_row_value(row, "order_date", "date")),
                    product_id=str(get_row_value(row, "product_id", "sku", "item_id") or ""),
                    size=str(get_row_value(row, "size") or ""),
                    price_paid=parse_float(get_row_value(row, "price_paid", "price", "paid")) or 0.0,
                    customer_id=str(get_row_value(row, "customer_id", "customer") or ""),
                )
                orders[order.order_id] = order
        return orders

    def get_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(str(order_id))

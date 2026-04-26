from __future__ import annotations

import csv
from pathlib import Path

from app.schemas.domain import Product, ProductSearchFilters
from app.utils.parsers import (
    get_row_value,
    normalize_size,
    normalize_text,
    parse_bool,
    parse_float,
    parse_list_field,
    parse_stock_map,
)


class ProductRepository:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self._products = self._load_products()

    def _load_products(self) -> dict[str, Product]:
        products: dict[str, Product] = {}
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                product = self._parse_product(row)
                products[product.product_id] = product
        return products

    def _parse_product(self, row: dict[str, str]) -> Product:
        tags = parse_list_field(get_row_value(row, "tags", "product_tags"))
        sizes_available = [
            normalize_size(size)
            for size in parse_list_field(get_row_value(row, "sizes_available", "sizes"))
            if normalize_size(size)
        ]
        stock_per_size = parse_stock_map(get_row_value(row, "stock_per_size", "stock", "inventory_by_size"))
        if not sizes_available and stock_per_size:
            sizes_available = list(stock_per_size.keys())

        return Product(
            product_id=str(get_row_value(row, "product_id", "id") or ""),
            title=str(get_row_value(row, "title", "name") or ""),
            vendor=str(get_row_value(row, "vendor", "brand") or ""),
            price=parse_float(get_row_value(row, "price")) or 0.0,
            compare_at_price=parse_float(get_row_value(row, "compare_at_price", "compareprice", "msrp")),
            tags=tags,
            sizes_available=sizes_available,
            stock_per_size=stock_per_size,
            is_sale=parse_bool(get_row_value(row, "is_sale", "sale")),
            is_clearance=parse_bool(get_row_value(row, "is_clearance", "clearance")),
            bestseller_score=parse_float(get_row_value(row, "bestseller_score", "bestseller", "score")) or 0.0,
        )

    def list_all(self) -> list[Product]:
        return list(self._products.values())

    def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(str(product_id))

    def stock_for_size(self, product: Product, size: str | None) -> int | None:
        if not size:
            return None
        normalized_size = normalize_size(size)
        if normalized_size in product.stock_per_size:
            return product.stock_per_size[normalized_size]
        if normalized_size in {normalize_size(item) for item in product.sizes_available}:
            return 0
        return None

    def search(self, filters: ProductSearchFilters) -> list[Product]:
        requested_tags = {normalize_text(tag) for tag in filters.tags if normalize_text(tag)}
        requested_size = normalize_size(filters.size) if filters.size else None
        requested_vendor = normalize_text(filters.vendor) if filters.vendor else None

        matches: list[Product] = []
        for product in self._products.values():
            if filters.max_price is not None and product.price > filters.max_price:
                continue
            if filters.min_price is not None and product.price < filters.min_price:
                continue
            if filters.sale_only and not product.is_sale:
                continue
            if requested_vendor and requested_vendor not in normalize_text(product.vendor):
                continue

            normalized_tags = {normalize_text(tag) for tag in product.tags}
            if requested_tags and not requested_tags.issubset(normalized_tags):
                continue

            if requested_size:
                stock = self.stock_for_size(product, requested_size)
                if stock is None or stock <= 0:
                    continue

            matches.append(product)

        return matches

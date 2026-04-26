from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    product_id: str
    title: str
    vendor: str
    price: float
    compare_at_price: float | None = None
    tags: list[str] = Field(default_factory=list)
    sizes_available: list[str] = Field(default_factory=list)
    stock_per_size: dict[str, int] = Field(default_factory=dict)
    is_sale: bool = False
    is_clearance: bool = False
    bestseller_score: float = 0.0


class Order(BaseModel):
    order_id: str
    order_date: date
    product_id: str
    size: str
    price_paid: float
    customer_id: str


class ProductSearchFilters(BaseModel):
    max_price: float | None = Field(default=None, description="Maximum product price in USD.")
    min_price: float | None = Field(default=None, description="Minimum product price in USD.")
    size: str | None = Field(default=None, description="Requested clothing size, such as 8 or M.")
    tags: list[str] = Field(
        default_factory=list,
        description="Desired product tags such as modest, evening, sleeve, fitted.",
    )
    sale_only: bool = Field(default=False, description="Return only sale items when true.")
    vendor: str | None = Field(default=None, description="Optional preferred vendor name.")
    limit: int = Field(default=5, ge=1, le=10, description="Maximum number of products to return.")

    @field_validator("size", "vendor", mode="before")
    @classmethod
    def coerce_optional_string(cls, value):
        if value is None:
            return None
        return str(value)


class ProductSearchResult(BaseModel):
    product_id: str
    title: str
    vendor: str
    price: float
    compare_at_price: float | None = None
    is_sale: bool
    is_clearance: bool
    bestseller_score: float
    matched_tags: list[str] = Field(default_factory=list)
    requested_size: str | None = None
    stock_for_requested_size: int | None = None
    ranking_score: float
    recommendation_reason: str


class ReturnEvaluation(BaseModel):
    order_found: bool
    product_found: bool
    order_id: str
    product_id: str | None = None
    decision: Literal["approved", "denied", "not_found", "manual_review"]
    eligible: bool | None = None
    reason: str
    days_since_order: int | None = None
    allowed_window_days: int | None = None
    ordered_size: str | None = None
    applied_rules: list[str] = Field(default_factory=list)
    exchange_option: str | None = None


class AgentAnswer(BaseModel):
    answer: str
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)

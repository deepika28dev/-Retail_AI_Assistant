from pydantic import BaseModel, Field, field_validator

from app.schemas.domain import ProductSearchFilters


class SearchProductsArgs(ProductSearchFilters):
    pass


class GetProductArgs(BaseModel):
    product_id: str = Field(..., description="The product identifier from the inventory.")

    @field_validator("product_id", mode="before")
    @classmethod
    def coerce_product_id(cls, value):
        return str(value)


class GetOrderArgs(BaseModel):
    order_id: str = Field(..., description="The order identifier from the orders file.")

    @field_validator("order_id", mode="before")
    @classmethod
    def coerce_order_id(cls, value):
        return str(value)


class EvaluateReturnArgs(BaseModel):
    order_id: str = Field(..., description="The order identifier to evaluate for return eligibility.")

    @field_validator("order_id", mode="before")
    @classmethod
    def coerce_order_id(cls, value):
        return str(value)

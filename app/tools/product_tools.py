from __future__ import annotations

from app.repositories.product_repository import ProductRepository
from app.schemas.domain import ProductSearchFilters, ProductSearchResult
from app.utils.parsers import normalize_size, normalize_text


class ProductTools:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def search_products(self, filters: ProductSearchFilters) -> dict:
        matches = self.product_repository.search(filters)
        ranked_results: list[ProductSearchResult] = []

        requested_tags = {normalize_text(tag) for tag in filters.tags if normalize_text(tag)}
        requested_size = normalize_size(filters.size) if filters.size else None

        for product in matches:
            stock_for_size = self.product_repository.stock_for_size(product, requested_size)
            matched_tags = [
                tag for tag in product.tags if normalize_text(tag) in requested_tags
            ]
            ranking_score = self._ranking_score(
                price=product.price,
                max_price=filters.max_price,
                is_sale=product.is_sale,
                bestseller_score=product.bestseller_score,
                matched_tag_count=len(matched_tags),
                stock_for_size=stock_for_size,
            )
            ranked_results.append(
                ProductSearchResult(
                    product_id=product.product_id,
                    title=product.title,
                    vendor=product.vendor,
                    price=product.price,
                    compare_at_price=product.compare_at_price,
                    is_sale=product.is_sale,
                    is_clearance=product.is_clearance,
                    bestseller_score=product.bestseller_score,
                    matched_tags=matched_tags,
                    requested_size=requested_size,
                    stock_for_requested_size=stock_for_size,
                    ranking_score=round(ranking_score, 2),
                    recommendation_reason=self._recommendation_reason(
                        product=product,
                        requested_size=requested_size,
                        stock_for_size=stock_for_size,
                        matched_tags=matched_tags,
                    ),
                )
            )

        ranked_results.sort(
            key=lambda item: (
                item.ranking_score,
                item.bestseller_score,
                1 if item.is_sale else 0,
                -item.price,
            ),
            reverse=True,
        )

        return {
            "filters_used": filters.model_dump(),
            "count": len(ranked_results),
            "products": [item.model_dump() for item in ranked_results[: filters.limit]],
        }

    def get_product(self, product_id: str) -> dict:
        product = self.product_repository.get_by_id(product_id)
        if product is None:
            return {
                "found": False,
                "product_id": str(product_id),
                "message": "Product not found.",
            }
        return {
            "found": True,
            "product": product.model_dump(),
        }

    @staticmethod
    def _ranking_score(
        *,
        price: float,
        max_price: float | None,
        is_sale: bool,
        bestseller_score: float,
        matched_tag_count: int,
        stock_for_size: int | None,
    ) -> float:
        score = bestseller_score
        if is_sale:
            score += 20
        score += matched_tag_count * 10
        if stock_for_size is not None and stock_for_size > 0:
            score += 15
        if max_price is not None and max_price > 0:
            score += max((max_price - price) / max_price * 10, 0)
        return score

    @staticmethod
    def _recommendation_reason(*, product, requested_size, stock_for_size, matched_tags: list[str]) -> str:
        reasons: list[str] = [f"Price is ${product.price:.2f}."]
        if requested_size:
            reasons.append(
                f"Requested size {requested_size} has {stock_for_size or 0} units in stock."
            )
        if matched_tags:
            reasons.append(f"Matched tags: {', '.join(matched_tags)}.")
        if product.is_sale:
            reasons.append("This item is on sale.")
        reasons.append(f"Bestseller score is {product.bestseller_score}.")
        return " ".join(reasons)

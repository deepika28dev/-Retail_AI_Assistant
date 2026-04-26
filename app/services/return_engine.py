from __future__ import annotations

from datetime import date

from app.repositories.order_repository import OrderRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.domain import ReturnEvaluation


class ReturnDecisionEngine:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        policy_repository: PolicyRepository,
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.policy_repository = policy_repository

    def evaluate_return(self, order_id: str) -> ReturnEvaluation:
        order = self.order_repository.get_by_id(order_id)
        if order is None:
            return ReturnEvaluation(
                order_found=False,
                product_found=False,
                order_id=str(order_id),
                decision="not_found",
                reason="The order ID was not found, so I cannot evaluate a return.",
            )

        product = self.product_repository.get_by_id(order.product_id)
        if product is None:
            return ReturnEvaluation(
                order_found=True,
                product_found=False,
                order_id=order.order_id,
                product_id=order.product_id,
                decision="not_found",
                reason="The order exists, but the related product was not found in inventory data.",
            )

        days_since_order = (date.today() - order.order_date).days
        applied_rules: list[str] = []

        normal_clause = self.policy_repository.find_normal_return_clause()
        normal_window_days = self.policy_repository.extract_days(normal_clause)
        if normal_clause:
            applied_rules.append(normal_clause)

        allowed_window_days = normal_window_days
        blocked = False
        exchange_option: str | None = None

        sale_clause = self.policy_repository.find_keyword_clause("sale") if product.is_sale else None
        if sale_clause:
            applied_rules.append(sale_clause)
            if self.policy_repository.blocks_return(sale_clause):
                blocked = True
            sale_window = self.policy_repository.extract_days(sale_clause)
            if sale_window is not None:
                allowed_window_days = self._pick_stricter_window(allowed_window_days, sale_window)
            if self.policy_repository.is_exchange_only(sale_clause):
                exchange_option = "This sale item appears to be exchange-only under the policy."

        clearance_clause = (
            self.policy_repository.find_keyword_clause("clearance") if product.is_clearance else None
        )
        if clearance_clause:
            applied_rules.append(clearance_clause)
            if self.policy_repository.blocks_return(clearance_clause):
                blocked = True
            clearance_window = self.policy_repository.extract_days(clearance_clause)
            if clearance_window is not None:
                allowed_window_days = self._pick_stricter_window(allowed_window_days, clearance_window)
            if self.policy_repository.is_exchange_only(clearance_clause):
                exchange_option = "This clearance item appears to be exchange-only under the policy."

        vendor_clauses = self.policy_repository.find_vendor_clauses(product.vendor)
        for vendor_clause in vendor_clauses:
            applied_rules.append(vendor_clause)
            if self.policy_repository.blocks_return(vendor_clause):
                blocked = True
            vendor_window = self.policy_repository.extract_days(vendor_clause)
            if vendor_window is not None:
                allowed_window_days = self._pick_stricter_window(allowed_window_days, vendor_window)
            if self.policy_repository.is_exchange_only(vendor_clause):
                exchange_option = f"Vendor policy for {product.vendor} appears to allow exchange only."

        exchange_clause = self.policy_repository.find_exchange_clause()
        if exchange_clause and exchange_clause not in applied_rules:
            applied_rules.append(exchange_clause)
            if exchange_option is None and self.policy_repository.is_exchange_only(exchange_clause):
                exchange_option = "The policy includes an exchange-only rule."

        if blocked:
            return ReturnEvaluation(
                order_found=True,
                product_found=True,
                order_id=order.order_id,
                product_id=product.product_id,
                decision="denied",
                eligible=False,
                reason="The policy marks this order as non-returnable based on sale, clearance, or vendor rules.",
                days_since_order=days_since_order,
                allowed_window_days=allowed_window_days,
                ordered_size=order.size,
                applied_rules=applied_rules,
                exchange_option=exchange_option,
            )

        if allowed_window_days is None:
            return ReturnEvaluation(
                order_found=True,
                product_found=True,
                order_id=order.order_id,
                product_id=product.product_id,
                decision="manual_review",
                eligible=None,
                reason="I could not find a clear return window in the policy text, so the case needs manual review.",
                days_since_order=days_since_order,
                allowed_window_days=None,
                ordered_size=order.size,
                applied_rules=applied_rules,
                exchange_option=exchange_option,
            )

        if days_since_order > allowed_window_days:
            return ReturnEvaluation(
                order_found=True,
                product_found=True,
                order_id=order.order_id,
                product_id=product.product_id,
                decision="denied",
                eligible=False,
                reason=(
                    f"The order is outside the allowed return window. "
                    f"It was placed {days_since_order} days ago and the policy allows {allowed_window_days} days."
                ),
                days_since_order=days_since_order,
                allowed_window_days=allowed_window_days,
                ordered_size=order.size,
                applied_rules=applied_rules,
                exchange_option=exchange_option,
            )

        return ReturnEvaluation(
            order_found=True,
            product_found=True,
            order_id=order.order_id,
            product_id=product.product_id,
            decision="approved",
            eligible=True,
            reason=(
                f"The order falls within the return window. "
                f"It was placed {days_since_order} days ago and the policy allows {allowed_window_days} days."
            ),
            days_since_order=days_since_order,
            allowed_window_days=allowed_window_days,
            ordered_size=order.size,
            applied_rules=applied_rules,
            exchange_option=exchange_option,
        )

    @staticmethod
    def _pick_stricter_window(current_window: int | None, candidate_window: int) -> int:
        if current_window is None:
            return candidate_window
        return min(current_window, candidate_window)

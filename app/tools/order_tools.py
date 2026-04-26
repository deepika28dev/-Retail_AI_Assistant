from __future__ import annotations

from app.repositories.order_repository import OrderRepository
from app.services.return_engine import ReturnDecisionEngine


class OrderTools:
    def __init__(self, order_repository: OrderRepository, return_engine: ReturnDecisionEngine):
        self.order_repository = order_repository
        self.return_engine = return_engine

    def get_order(self, order_id: str) -> dict:
        order = self.order_repository.get_by_id(order_id)
        if order is None:
            return {
                "found": False,
                "order_id": str(order_id),
                "message": "Order not found.",
            }
        return {
            "found": True,
            "order": order.model_dump(mode="json"),
        }

    def evaluate_return(self, order_id: str) -> dict:
        evaluation = self.return_engine.evaluate_return(order_id)
        return evaluation.model_dump(mode="json")

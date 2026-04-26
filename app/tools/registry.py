from __future__ import annotations

import json
from typing import Any, Callable

from app.schemas.tools import EvaluateReturnArgs, GetOrderArgs, GetProductArgs, SearchProductsArgs
from app.tools.order_tools import OrderTools
from app.tools.product_tools import ProductTools


class ToolRegistry:
    def __init__(self, product_tools: ProductTools, order_tools: OrderTools):
        self.product_tools = product_tools
        self.order_tools = order_tools

        self._tool_map: dict[str, tuple[type, Callable[..., dict]]] = {
            "search_products": (SearchProductsArgs, self._run_search_products),
            "get_product": (GetProductArgs, self._run_get_product),
            "get_order": (GetOrderArgs, self._run_get_order),
            "evaluate_return": (EvaluateReturnArgs, self._run_evaluate_return),
        }

    def openai_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": (
                        "Search the product inventory using business filters. "
                        "Use this for shopping or recommendation requests."
                    ),
                    "parameters": SearchProductsArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product",
                    "description": "Fetch one product by product_id. Use this to confirm product details.",
                    "parameters": GetProductArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order",
                    "description": "Fetch one order by order_id. Use this before reasoning about support cases.",
                    "parameters": GetOrderArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_return",
                    "description": (
                        "Evaluate whether an order can be returned by combining order data, "
                        "product attributes, and policy rules."
                    ),
                    "parameters": EvaluateReturnArgs.model_json_schema(),
                },
            },
        ]

    def execute(self, name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
        if name not in self._tool_map:
            raise ValueError(f"Unsupported tool: {name}")

        args_model, handler = self._tool_map[name]
        payload = json.loads(arguments) if isinstance(arguments, str) else arguments
        validated_payload = args_model.model_validate(payload)
        return handler(validated_payload)

    def _run_search_products(self, args: SearchProductsArgs) -> dict[str, Any]:
        return self.product_tools.search_products(args)

    def _run_get_product(self, args: GetProductArgs) -> dict[str, Any]:
        return self.product_tools.get_product(args.product_id)

    def _run_get_order(self, args: GetOrderArgs) -> dict[str, Any]:
        return self.order_tools.get_order(args.order_id)

    def _run_evaluate_return(self, args: EvaluateReturnArgs) -> dict[str, Any]:
        return self.order_tools.evaluate_return(args.order_id)

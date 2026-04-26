from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.agent.orchestrator import RetailAgent
from app.config import Settings, get_settings
from app.repositories.order_repository import OrderRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.product_repository import ProductRepository
from app.services.return_engine import ReturnDecisionEngine
from app.tools.order_tools import OrderTools
from app.tools.product_tools import ProductTools
from app.tools.registry import ToolRegistry


@dataclass
class AppContainer:
    settings: Settings
    product_repository: ProductRepository
    order_repository: OrderRepository
    policy_repository: PolicyRepository
    return_engine: ReturnDecisionEngine
    product_tools: ProductTools
    order_tools: OrderTools
    tool_registry: ToolRegistry
    agent: RetailAgent


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    settings = get_settings()
    product_repository = ProductRepository(settings.products_csv_path)
    order_repository = OrderRepository(settings.orders_csv_path)
    policy_repository = PolicyRepository(settings.policy_path)
    return_engine = ReturnDecisionEngine(order_repository, product_repository, policy_repository)
    product_tools = ProductTools(product_repository)
    order_tools = OrderTools(order_repository, return_engine)
    tool_registry = ToolRegistry(product_tools, order_tools)
    agent = RetailAgent(settings, tool_registry)
    return AppContainer(
        settings=settings,
        product_repository=product_repository,
        order_repository=order_repository,
        policy_repository=policy_repository,
        return_engine=return_engine,
        product_tools=product_tools,
        order_tools=order_tools,
        tool_registry=tool_registry,
        agent=agent,
    )

from datetime import date, timedelta

from app.repositories.order_repository import OrderRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.product_repository import ProductRepository
from app.services.return_engine import ReturnDecisionEngine


def test_evaluate_return_approves_when_inside_window(tmp_path):
    recent_order_date = (date.today() - timedelta(days=7)).isoformat()
    products_csv = tmp_path / "products.csv"
    orders_csv = tmp_path / "orders.csv"
    policy_txt = tmp_path / "policy.txt"

    products_csv.write_text(
        "\n".join(
            [
                "product_id,title,vendor,price,compare_at_price,tags,sizes_available,stock_per_size,is_sale,is_clearance,bestseller_score",
                'P1,Evening Grace,Vera,250,320,"modest,evening","8|10","8:3|10:1",false,false,90',
            ]
        ),
        encoding="utf-8",
    )
    orders_csv.write_text(
        "\n".join(
            [
                "order_id,order_date,product_id,size,price_paid,customer_id",
                f"1043,{recent_order_date},P1,8,250,C100",
            ]
        ),
        encoding="utf-8",
    )
    policy_txt.write_text(
        "\n".join(
            [
                "Normal return window:",
                "30 days from the order date.",
                "Sale item return rules:",
                "Sale items are eligible for return within 14 days.",
                "Clearance rules:",
                "Clearance items cannot be returned.",
                "Exchange rules:",
                "Eligible items can be exchanged within the same window.",
            ]
        ),
        encoding="utf-8",
    )

    engine = ReturnDecisionEngine(
        OrderRepository(orders_csv),
        ProductRepository(products_csv),
        PolicyRepository(policy_txt),
    )

    result = engine.evaluate_return("1043")

    assert result.decision == "approved"
    assert result.eligible is True
    assert result.allowed_window_days == 30


def test_evaluate_return_denies_clearance_item(tmp_path):
    recent_order_date = (date.today() - timedelta(days=5)).isoformat()
    products_csv = tmp_path / "products.csv"
    orders_csv = tmp_path / "orders.csv"
    policy_txt = tmp_path / "policy.txt"

    products_csv.write_text(
        "\n".join(
            [
                "product_id,title,vendor,price,compare_at_price,tags,sizes_available,stock_per_size,is_sale,is_clearance,bestseller_score",
                'P9,Outlet Dress,Vera,99,199,"modest,clearance","8|10","8:2|10:1",true,true,70',
            ]
        ),
        encoding="utf-8",
    )
    orders_csv.write_text(
        "\n".join(
            [
                "order_id,order_date,product_id,size,price_paid,customer_id",
                f"2040,{recent_order_date},P9,8,99,C200",
            ]
        ),
        encoding="utf-8",
    )
    policy_txt.write_text(
        "\n".join(
            [
                "Normal return window: 30 days.",
                "Clearance rules:",
                "Clearance items cannot be returned.",
                "Exchange rules: Clearance items are exchange only.",
            ]
        ),
        encoding="utf-8",
    )

    engine = ReturnDecisionEngine(
        OrderRepository(orders_csv),
        ProductRepository(products_csv),
        PolicyRepository(policy_txt),
    )

    result = engine.evaluate_return("2040")

    assert result.decision == "denied"
    assert result.eligible is False
    assert "non-returnable" in result.reason or "policy" in result.reason.lower()

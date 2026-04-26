from app.repositories.product_repository import ProductRepository
from app.schemas.domain import ProductSearchFilters
from app.schemas.tools import SearchProductsArgs
from app.tools.product_tools import ProductTools


def test_search_products_filters_size_sale_and_tags(tmp_path):
    products_csv = tmp_path / "products.csv"
    products_csv.write_text(
        "\n".join(
            [
                "product_id,title,vendor,price,compare_at_price,tags,sizes_available,stock_per_size,is_sale,is_clearance,bestseller_score",
                'P1,Evening Grace,Vera,250,320,"modest,evening","8|10","8:3|10:1",true,false,90',
                'P2,Satin Night,Luna,280,280,"evening,fitted","8|12","8:0|12:2",false,false,80',
                'P3,Formal Bloom,Vera,310,350,"modest,evening","8|10","8:4|10:2",true,false,95',
            ]
        ),
        encoding="utf-8",
    )

    repository = ProductRepository(products_csv)
    tools = ProductTools(repository)

    result = tools.search_products(
        ProductSearchFilters(max_price=300, size="8", tags=["modest", "evening"], sale_only=True)
    )

    assert result["count"] == 1
    assert result["products"][0]["product_id"] == "P1"
    assert result["products"][0]["stock_for_requested_size"] == 3


def test_search_products_args_accepts_numeric_size():
    args = SearchProductsArgs.model_validate({"max_price": 300, "size": 8, "tags": ["modest"]})

    assert args.size == "8"

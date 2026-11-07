"""LangChain tools for the shopping assistant."""

import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))
BASE_URL = os.getenv("ECOMM_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
_SEARCH_STOP_WORDS = {
    "a", "an", "and", "for", "find", "get", "in", "me", "of", "options",
    "or", "product", "products", "show", "tell", "the", "to", "under",
    "with", "which",
}


def _request_json(path: str) -> Any:
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def _sentiment_summary(average_rating: float) -> str:
    if average_rating >= 4:
        sentiment = "positive"
    elif average_rating >= 3:
        sentiment = "mixed"
    else:
        sentiment = "negative"
    return f"{average_rating:.1f}/5 average; {sentiment} sentiment"


@tool
def CatalogSearch(query: str) -> str:
    """Search the product catalogue by a free-form query string.

    Returns a JSON list of matching products (id, name, category, description).
    Use this tool to find products that match a user's shopping query.
    """
    products = _request_json("/products")
    terms = [
        term.lower()
        for term in re.findall(r"[a-zA-Z]+", query)
        if term.lower() not in _SEARCH_STOP_WORDS
    ]
    if not terms:
        return json.dumps(products if not query.strip() else [])

    return json.dumps(
        [
            product
            for product in products
            if any(
                term in (
                    f"{product['name']} {product['category']} "
                    f"{product['description']}"
                ).lower()
                for term in terms
            )
        ]
    )


@tool
def PricingAPI(product_id: str) -> str:
    """Get the price and currency for a given product_id.

    Returns JSON with product_id, price, currency, and discount (always 'No discount').
    """
    data = _request_json(f"/price/{product_id}")
    data["discount"] = "No discount"
    data["price"] = f"{data['price']:.2f} {data['currency']}"
    return json.dumps(data)


@tool
def InventoryAPI(product_id: str) -> str:
    """Get stock availability and quantity for a given product_id.

    Returns JSON with product_id, in_stock (boolean), quantity.
    """
    return json.dumps(_request_json(f"/availability/{product_id}"))


@tool
def ReviewAPI(product_id: str) -> str:
    """Get average rating, review count, and sentiment summary by product ID.

    Returns only a concise review summary; raw comments are not sent to the model.
    """
    data = _request_json(f"/reviews/{product_id}")
    average_rating = float(data["rating"])
    return json.dumps({
        "product_id": str(data["product_id"]),
        "average_rating": average_rating,
        "review_count": len(data["reviews"]),
        "sentiment_summary": _sentiment_summary(average_rating),
    })

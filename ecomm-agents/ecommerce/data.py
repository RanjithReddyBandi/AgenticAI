"""Default and edge-case fixture data for the ecommerce API."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_DATA: dict[str, dict[int, Any] | list[dict[str, Any]]] = {
    "products": [
        {"id": 1, "name": "belt", "category": "accessories", "description": "A classic leather belt for everyday wear."},
        {"id": 2, "name": "shoes", "category": "footwear", "description": "Comfortable running shoes with breathable mesh."},
        {"id": 3, "name": "wallet", "category": "accessories", "description": "A slim bi-fold wallet with multiple card slots."},
        {"id": 4, "name": "jacket", "category": "apparel", "description": "A waterproof winter jacket with insulated lining."},
    ],
    "prices": {
        1: {"product_id": 1, "price": 29.99, "currency": "USD"},
        2: {"product_id": 2, "price": 79.50, "currency": "USD"},
        3: {"product_id": 3, "price": 19.99, "currency": "USD"},
        4: {"product_id": 4, "price": 149.99, "currency": "USD"},
    },
    "availability": {
        1: {"product_id": 1, "in_stock": True, "quantity": 150},
        2: {"product_id": 2, "in_stock": True, "quantity": 42},
        3: {"product_id": 3, "in_stock": False, "quantity": 0},
        4: {"product_id": 4, "in_stock": True, "quantity": 8},
    },
    "reviews": {
        1: {"product_id": 1, "reviews": [{"comment": "Great belt, fits perfectly.", "rating": 5}, {"comment": "Good quality for the price.", "rating": 4}]},
        2: {"product_id": 2, "reviews": [{"comment": "Very comfortable, perfect for running.", "rating": 5}, {"comment": "Nice design but runs a bit small.", "rating": 3}, {"comment": "Best shoes I have ever bought.", "rating": 5}]},
        3: {"product_id": 3, "reviews": [{"comment": "Sleek and functional.", "rating": 4}, {"comment": "Card slots are a bit tight.", "rating": 3}]},
        4: {"product_id": 4, "reviews": [{"comment": "Keeps me warm even in freezing weather.", "rating": 5}, {"comment": "Slightly heavy for everyday use.", "rating": 3}]},
    },
}

EDGE_DATA: dict[str, dict[int, Any] | list[dict[str, Any]]] = {
    "products": [
        {"id": 101, "name": "black leather jacket", "category": "apparel", "description": "Black leather jacket with a quilted lining."},
        {"id": 102, "name": "brown leather jacket", "category": "apparel", "description": "Brown leather jacket with a removable hood."},
        {"id": 103, "name": "black jacket", "category": "apparel", "description": "Black waterproof jacket; material is not specified."},
        {"id": 104, "name": "black leather belt", "category": "accessories", "description": "Black leather belt with a brushed metal buckle."},
        {"id": 105, "name": "brown leather belt", "category": "accessories", "description": "Brown leather belt with a reversible strap."},
        {"id": 106, "name": "leather wallet", "category": "accessories", "description": "Compact black leather wallet with six card slots."},
        {"id": 107, "name": "canvas wallet", "category": "accessories", "description": "Lightweight canvas wallet with a zip pocket."},
        {"id": 108, "name": "silk scarf", "category": "accessories", "description": "Purple silk scarf with a floral pattern."},
        {"id": 109, "name": "wool hat", "category": "accessories", "description": "Purple wool hat with a ribbed knit."},
        {"id": 110, "name": "running shoes", "category": "footwear", "description": "Breathable mesh running shoes with cushioned soles."},
    ],
    "prices": {
        101: {"product_id": 101, "price": 100.00, "currency": "USD"},
        102: {"product_id": 102, "price": 100.01, "currency": "USD"},
        103: {"product_id": 103, "price": 89.99, "currency": "USD"},
        104: {"product_id": 104, "price": 50.00, "currency": "USD"},
        105: {"product_id": 105, "price": 49.99, "currency": "USD"},
        106: {"product_id": 106, "price": 35.00, "currency": "USD"},
        107: {"product_id": 107, "price": 40.01, "currency": "USD"},
        108: {"product_id": 108, "price": 45.00, "currency": "USD"},
        109: {"product_id": 109, "price": 25.00, "currency": "USD"},
        110: {"product_id": 110, "price": 79.50, "currency": "USD"},
    },
    "availability": {
        101: {"product_id": 101, "in_stock": True, "quantity": 3},
        102: {"product_id": 102, "in_stock": False, "quantity": 0},
        103: {"product_id": 103, "in_stock": True, "quantity": 1},
        104: {"product_id": 104, "in_stock": True, "quantity": 12},
        105: {"product_id": 105, "in_stock": True, "quantity": 0},
        106: {"product_id": 106, "in_stock": True, "quantity": 1},
        107: {"product_id": 107, "in_stock": True, "quantity": 5},
        108: {"product_id": 108, "in_stock": False, "quantity": 0},
        109: {"product_id": 109, "in_stock": True, "quantity": 8},
        110: {"product_id": 110, "in_stock": True, "quantity": 42},
    },
    "reviews": {
        101: {"product_id": 101, "reviews": [{"comment": "Excellent fit and finish.", "rating": 5}, {"comment": "Good but expensive.", "rating": 4}]},
        102: {"product_id": 102, "reviews": [{"comment": "Leather feels stiff.", "rating": 2}, {"comment": "Poor stitching.", "rating": 1}]},
        103: {"product_id": 103, "reviews": [{"comment": "Keeps out the rain.", "rating": 4}, {"comment": "Sizing is inconsistent.", "rating": 2}]},
        104: {"product_id": 104, "reviews": [{"comment": "Great value.", "rating": 5}, {"comment": "Buckle scratched quickly.", "rating": 3}]},
        105: {"product_id": 105, "reviews": [{"comment": "Comfortable and sturdy.", "rating": 5}, {"comment": "Looks good.", "rating": 4}]},
        106: {"product_id": 106, "reviews": [{"comment": "Useful layout.", "rating": 4}, {"comment": "A bit stiff.", "rating": 3}]},
        107: {"product_id": 107, "reviews": [{"comment": "Falls apart quickly.", "rating": 1}, {"comment": "Not as described.", "rating": 2}]},
        108: {"product_id": 108, "reviews": [{"comment": "Soft silk and vivid color.", "rating": 5}, {"comment": "Lovely pattern.", "rating": 5}]},
        109: {"product_id": 109, "reviews": [{"comment": "Warm and comfortable.", "rating": 4}, {"comment": "Nice knit.", "rating": 5}]},
        110: {"product_id": 110, "reviews": [{"comment": "Very comfortable for running.", "rating": 5}, {"comment": "Wears down quickly.", "rating": 2}]},
    },
}


DATASET_NAME = os.getenv("ECOMM_MOCK_DATA", "default").strip().lower()
DATASETS = {"default": DEFAULT_DATA, "edge": EDGE_DATA}
if DATASET_NAME not in DATASETS:
    raise ValueError(
        f"Unknown ECOMM_MOCK_DATA value {DATASET_NAME!r}; choose 'default' or 'edge'."
    )

_selected_data = DATASETS[DATASET_NAME]
PRODUCTS = _selected_data["products"]
PRICES = _selected_data["prices"]
AVAILABILITY = _selected_data["availability"]
REVIEWS = _selected_data["reviews"]

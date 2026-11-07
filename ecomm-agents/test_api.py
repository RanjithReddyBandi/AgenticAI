"""Smoke test for the mock ecommerce API."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from ecommerce.main import app


def main() -> None:
    client = TestClient(app)
    failures = 0

    # Root endpoint
    resp = client.get("/")
    assert resp.status_code == 200, f"Root failed: {resp.status_code}"
    print("GET / -> OK")

    # Product catalogue
    resp = client.get("/products")
    assert resp.status_code == 200, f"Catalogue failed: {resp.status_code}"
    products = resp.json()
    assert len(products) == 4, f"Expected 4 products, got {len(products)}"
    names = {p["name"] for p in products}
    assert {"belt", "shoes", "wallet", "jacket"} <= names, f"Missing products: {names}"
    print("GET /products -> OK")

    # Price
    resp = client.get("/price/1")
    assert resp.status_code == 200, f"Price 1 failed: {resp.status_code}"
    price = resp.json()
    assert price["product_id"] == 1 and price["price"] == 29.99, f"Unexpected price: {price}"
    print("GET /price/1 -> OK")

    # Price invalid
    resp = client.get("/price/999")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("GET /price/999 -> 404 OK")

    # Availability
    resp = client.get("/availability/3")
    assert resp.status_code == 200, f"Availability 3 failed: {resp.status_code}"
    avail = resp.json()
    assert avail["in_stock"] is False and avail["quantity"] == 0, f"Unexpected: {avail}"
    print("GET /availability/3 -> OK")

    # Reviews
    resp = client.get("/reviews/2")
    assert resp.status_code == 200, f"Reviews 2 failed: {resp.status_code}"
    reviews = resp.json()
    assert len(reviews["reviews"]) == 3, f"Expected 3 reviews, got {len(reviews['reviews'])}"
    assert 1 <= reviews["rating"] <= 5, f"Rating out of range: {reviews['rating']}"
    print("GET /reviews/2 -> OK")

    print("\nAll tests passed!")


if __name__ == "__main__":
    main()

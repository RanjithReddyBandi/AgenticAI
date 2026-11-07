"""Price API router."""
from fastapi import APIRouter, HTTPException

from .models import Price
from .data import PRICES

router = APIRouter(prefix="/price", tags=["price"])


@router.get("/{product_id}", response_model=Price)
async def get_price(product_id: int) -> Price:
    """Return the price for a given product ID."""
    price = PRICES.get(product_id)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return Price(**price)

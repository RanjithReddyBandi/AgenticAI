"""Product Catalogue API router."""
from fastapi import APIRouter, HTTPException

from .models import Product
from .data import PRODUCTS

router = APIRouter(prefix="/products", tags=["catalogue"])


@router.get("", response_model=list[Product])
async def list_products() -> list[Product]:
    """Return the full list of products."""
    return [Product(**p) for p in PRODUCTS]

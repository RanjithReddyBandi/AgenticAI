"""Availability API router."""
from fastapi import APIRouter, HTTPException

from .models import Availability
from .data import AVAILABILITY

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("/{product_id}", response_model=Availability)
async def get_availability(product_id: int) -> Availability:
    """Return the stock availability for a given product ID."""
    availability = AVAILABILITY.get(product_id)
    if availability is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return Availability(**availability)

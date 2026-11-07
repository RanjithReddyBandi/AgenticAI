"""Review Comments API router."""
from fastapi import APIRouter, HTTPException

from .models import Reviews
from .data import REVIEWS

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{product_id}", response_model=Reviews)
async def get_reviews(product_id: int) -> Reviews:
    """Return the reviews for a given product ID."""
    review_data = REVIEWS.get(product_id)
    if review_data is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    review_items = review_data["reviews"]
    average_rating = sum(review["rating"] for review in review_items) / len(review_items)
    return Reviews(
        product_id=product_id,
        reviews=review_items,
        rating=round(average_rating, 1),
    )

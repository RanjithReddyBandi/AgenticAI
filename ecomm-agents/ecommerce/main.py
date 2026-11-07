"""Main FastAPI application for the mock ecommerce API."""
from fastapi import FastAPI

from .catalogue import router as catalogue_router
from .price import router as price_router
from .availability import router as availability_router
from .reviews import router as reviews_router

app = FastAPI(
    title="Mock Ecommerce API",
    description="A clean FastAPI project simulating ecommerce APIs for agentic AI app development.",
    version="1.0.0",
)

app.include_router(catalogue_router)
app.include_router(price_router)
app.include_router(availability_router)
app.include_router(reviews_router)


@app.get("/")
async def root() -> dict:
    """Return a friendly welcome message."""
    return {"message": "Welcome to the Mock Ecommerce API. See /docs for the API documentation."}

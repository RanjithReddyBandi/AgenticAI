"""Pydantic models for the ecommerce API."""
from pydantic import BaseModel, Field
from typing import List


class Product(BaseModel):
    """A product in the catalogue."""
    id: int = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    description: str = Field(..., description="Product description")


class Price(BaseModel):
    """Price information for a product."""
    product_id: int = Field(..., description="Product identifier")
    price: float = Field(..., description="Product price")
    currency: str = Field(..., description="Currency code")


class Availability(BaseModel):
    """Stock availability for a product."""
    product_id: int = Field(..., description="Product identifier")
    in_stock: bool = Field(..., description="Whether the product is in stock")
    quantity: int = Field(..., description="Available quantity")


class Review(BaseModel):
    """A single review comment."""
    comment: str = Field(..., description="Review text")
    rating: int = Field(..., description="Rating from 1 to 5")


class Reviews(BaseModel):
    """Collection of reviews for a product."""
    product_id: int = Field(..., description="Product identifier")
    reviews: List[Review] = Field(..., description="List of review comments")
    rating: float = Field(..., description="Average rating from 1 to 5")

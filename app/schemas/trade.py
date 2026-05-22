"""Trade schemas."""
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional, List, Literal
from datetime import datetime

from app.schemas.card import Card


class TradeItemCreate(BaseModel):
    """Schema for creating a trade item."""
    card_id: UUID
    qty: int = Field(default=1, ge=1)
    condition: str = "NM"
    language: str = "EN"
    user_photos: Optional[List[dict]] = None


class TradeItem(BaseModel):
    """Schema for trade item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    side: Literal["offer", "want"]
    card_id: UUID
    qty: int
    condition: str
    language: str
    user_photos: Optional[List[dict]] = None
    card: Optional[Card] = None


class TradeItemLite(BaseModel):
    """Lightweight trade item for feed (no user_photos to reduce payload size)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    side: Literal["offer", "want"]
    card_id: UUID
    qty: int
    condition: str
    language: str
    card: Optional[Card] = None


class TradeCreate(BaseModel):
    """Schema for creating a trade."""
    title: str = Field(min_length=1, description="Title is required")
    notes: str = Field(min_length=1, description="Description is required")
    cash_amount_cents: Optional[int] = None
    post_type: Optional[Literal["TRADE", "SALE", "WTB"]] = "TRADE"
    offered_items: List[TradeItemCreate]
    wanted_items: List[TradeItemCreate]


class Trade(BaseModel):
    """Schema for trade response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    share_slug: str
    title: Optional[str] = None
    notes: Optional[str] = None
    cash_amount_cents: Optional[int] = None
    creator_user_id: Optional[UUID] = None
    created_at: datetime


class TradeDetail(Trade):
    """Schema for detailed trade response with items."""
    offered_items: List[TradeItem] = []
    wanted_items: List[TradeItem] = []


# Feed-specific schemas
class FeedItemSummary(BaseModel):
    """Summary of items for feed card."""
    offering: str  # e.g., "Charizard ex (NM)"
    requesting: str  # e.g., "3 cards + $65"


class FeedGeo(BaseModel):
    """Geographic information for feed."""
    country: str
    region: str
    domestic_only: bool


class FeedPost(BaseModel):
    """Schema for feed post (collapsed state)."""
    model_config = ConfigDict(from_attributes=True)

    post_id: UUID
    post_type: Literal["TRADE", "SALE", "WTB"]
    share_slug: str
    created_at: datetime
    creator_user_id: Optional[str] = None  # Cognito sub for ownership detection

    # Title, description, and creator info
    title: Optional[str] = None
    notes: Optional[str] = None
    creator_name: Optional[str] = None

    hero_image: Optional[str] = None
    summary: FeedItemSummary

    offered_items_count: int
    requested_items_count: int

    geo: FeedGeo
    quality_score: Optional[int] = None

    # Full item details for expansion (using lite version without user_photos)
    offered_items: List[TradeItemLite] = []
    requested_items: List[TradeItemLite] = []
    cash_adjustment: Optional[int] = None  # In cents


class FeedResponse(BaseModel):
    """Schema for feed API response."""
    posts: List[FeedPost]
    total: int
    has_more: bool


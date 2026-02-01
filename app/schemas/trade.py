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


class TradeItem(BaseModel):
    """Schema for trade item response."""
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
    title: Optional[str] = None
    notes: Optional[str] = None
    offered_items: List[TradeItemCreate]
    wanted_items: List[TradeItemCreate]


class Trade(BaseModel):
    """Schema for trade response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    share_slug: str
    title: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class TradeDetail(Trade):
    """Schema for detailed trade response with items."""
    offered_items: List[TradeItem] = []
    wanted_items: List[TradeItem] = []


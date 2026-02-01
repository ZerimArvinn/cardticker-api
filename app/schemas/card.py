"""Card schemas."""
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime


class CardBase(BaseModel):
    """Base card schema."""
    name: str
    set_name: str
    card_number: str
    rarity: Optional[str] = None
    image_url: Optional[str] = None


class CardCreate(CardBase):
    """Schema for creating a card."""
    game: str = "pokemon"
    external_ids: Optional[dict] = None


class Card(CardBase):
    """Schema for card response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    game: str
    external_ids: Optional[dict] = None
    created_at: datetime


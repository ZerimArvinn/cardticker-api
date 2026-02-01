"""Proposal schemas."""
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional, List, Literal
from datetime import datetime

from app.schemas.card import Card


class ProposalItemCreate(BaseModel):
    """Schema for creating a proposal item."""
    card_id: UUID
    qty: int = Field(default=1, ge=1)
    condition: str = "NM"
    language: str = "EN"


class ProposalItem(BaseModel):
    """Schema for proposal item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    side: Literal["offer", "want"]
    card_id: UUID
    qty: int
    condition: str
    language: str
    card: Optional[Card] = None


class ProposalCreate(BaseModel):
    """Schema for creating a proposal."""
    proposer_name: Optional[str] = None
    offered_items: List[ProposalItemCreate]
    wanted_items: List[ProposalItemCreate]


class Proposal(BaseModel):
    """Schema for proposal response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    trade_id: UUID
    proposer_name: Optional[str] = None
    status: str
    created_at: datetime


class ProposalScores(BaseModel):
    """Schema for proposal scoring results."""
    fairness_score: int = Field(ge=0, le=100)
    liquidity_score: int = Field(ge=0, le=100)
    volatility_score: int = Field(ge=0, le=100)
    
    proposer_offer_total_cents: int
    proposer_want_total_cents: int
    value_diff_cents: int
    value_diff_description: str
    
    explanation: List[str]


class ProposalDetail(Proposal):
    """Schema for detailed proposal response with items and scores."""
    offered_items: List[ProposalItem] = []
    wanted_items: List[ProposalItem] = []
    scores: Optional[ProposalScores] = None


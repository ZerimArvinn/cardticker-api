"""Trade and TradeItem models."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Trade(Base):
    """Trade post model."""

    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    cash_amount_cents = Column(Integer, nullable=True)  # Cash amount in cents (optional)
    share_slug = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Feed-specific fields
    post_type = Column(String, nullable=False, default="TRADE")  # TRADE, SALE, WTB
    hero_image_url = Column(Text, nullable=True)  # Primary image for feed card
    country = Column(String(2), nullable=False, default="US")  # ISO country code
    region = Column(String(50), nullable=False, default="US-East")  # Region within country
    domestic_only = Column(Boolean, nullable=False, default=False)  # Shipping restriction
    quality_score = Column(Integer, nullable=True)  # Completeness score 0-100
    view_count = Column(Integer, nullable=False, default=0)  # For ranking
    last_bumped_at = Column(DateTime(timezone=True), nullable=True)  # For freshness

    # Relationships
    items = relationship("TradeItem", back_populates="trade", cascade="all, delete-orphan")
    proposals = relationship("TradeProposal", back_populates="trade", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[creator_user_id])

    __table_args__ = (
        CheckConstraint("post_type IN ('TRADE', 'SALE', 'WTB')", name="trades_post_type_check"),
    )


class TradeItem(Base):
    """Items in a trade post (offered or wanted)."""

    __tablename__ = "trade_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id", ondelete="CASCADE"), nullable=False)
    side = Column(String, nullable=False)  # 'offer' or 'want'
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False)
    qty = Column(Integer, nullable=False, default=1)
    condition = Column(String, nullable=False, default="NM")  # NM/LP/MP/HP/DMG
    language = Column(String, nullable=False, default="EN")
    user_photos = Column(JSONB, nullable=True)  # [{"url": "...", "label": "Front"}, ...]
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("side IN ('offer', 'want')", name="trade_items_side_check"),
    )

    # Relationships
    trade = relationship("Trade", back_populates="items")
    card = relationship("Card")


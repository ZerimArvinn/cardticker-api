"""Trade and TradeItem models."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
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
    share_slug = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    items = relationship("TradeItem", back_populates="trade", cascade="all, delete-orphan")
    proposals = relationship("TradeProposal", back_populates="trade", cascade="all, delete-orphan")


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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("side IN ('offer', 'want')", name="trade_items_side_check"),
    )

    # Relationships
    trade = relationship("Trade", back_populates="items")
    card = relationship("Card")


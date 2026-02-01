"""PricePoint model."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class PricePoint(Base):
    """Price point for a card at a specific time."""
    
    __tablename__ = "price_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False)
    condition = Column(String, nullable=False, default="NM")
    source = Column(String, nullable=False, default="seed")  # 'seed', 'tcgplayer', 'ebay', etc.
    price_cents = Column(Integer, nullable=False)  # Store price in cents
    ts = Column(DateTime(timezone=True), nullable=False)  # Timestamp of the price point

    # Relationships
    card = relationship("Card")

    __table_args__ = (
        Index("idx_price_card_ts", "card_id", "ts"),
        Index("idx_price_card_condition_ts", "card_id", "condition", "ts"),
    )


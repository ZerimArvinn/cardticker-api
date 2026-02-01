"""TradeProposal and ProposalItem models."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class TradeProposal(Base):
    """Trade proposal model."""
    
    __tablename__ = "trade_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id", ondelete="CASCADE"), nullable=False)
    proposer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    proposer_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="submitted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    trade = relationship("Trade", back_populates="proposals")
    items = relationship("ProposalItem", back_populates="proposal", cascade="all, delete-orphan")


class ProposalItem(Base):
    """Items in a proposal (offered or wanted by proposer)."""
    
    __tablename__ = "proposal_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("trade_proposals.id", ondelete="CASCADE"), nullable=False)
    side = Column(String, nullable=False)  # 'offer' or 'want'
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False)
    qty = Column(Integer, nullable=False, default=1)
    condition = Column(String, nullable=False, default="NM")
    language = Column(String, nullable=False, default="EN")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("side IN ('offer', 'want')", name="proposal_items_side_check"),
    )

    # Relationships
    proposal = relationship("TradeProposal", back_populates="items")
    card = relationship("Card")


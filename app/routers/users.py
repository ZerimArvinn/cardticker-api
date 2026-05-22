"""Users router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.models.trade import Trade as TradeModel, TradeItem as TradeItemModel
from app.models.proposal import TradeProposal as ProposalModel
from app.models.user import User as UserModel
from app.schemas.trade import Trade, TradeDetail, TradeItem
from app.schemas.card import Card
from app.schemas.proposal import Proposal
from app.auth import require_auth

router = APIRouter()


class UserInfo(BaseModel):
    """Schema for user information."""
    id: UUID
    handle: str
    email: str


@router.get("/users/me", response_model=UserInfo)
def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Get current authenticated user's information."""
    # Get user from database
    user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserInfo(
        id=user.id,
        handle=user.handle,
        email=user.email
    )


@router.get("/users/me/trades", response_model=List[TradeDetail])
def get_my_trades(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Get all trades created by the authenticated user with full details."""
    # Get user from database
    user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
    if not user:
        return []

    # Get user's trades with eager loading of items and cards
    trades = db.query(TradeModel).options(
        joinedload(TradeModel.items).joinedload(TradeItemModel.card)
    ).filter(
        TradeModel.creator_user_id == user.id
    ).order_by(TradeModel.created_at.desc()).all()

    # Build detailed response with items
    result = []
    for trade in trades:
        offered_items = []
        wanted_items = []

        for item in trade.items:
            trade_item = TradeItem.model_validate(item)
            if item.card:
                trade_item.card = Card.model_validate(item.card)

            if item.side == "offer":
                offered_items.append(trade_item)
            else:
                wanted_items.append(trade_item)

        trade_detail = TradeDetail.model_validate(trade)
        trade_detail.offered_items = offered_items
        trade_detail.wanted_items = wanted_items
        result.append(trade_detail)

    return result


@router.get("/users/me/proposals", response_model=List[Proposal])
def get_my_proposals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Get all proposals made by the authenticated user."""
    # Get user from database
    user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
    if not user:
        return []

    # Get user's proposals
    proposals = db.query(ProposalModel).filter(
        ProposalModel.proposer_user_id == user.id
    ).order_by(ProposalModel.created_at.desc()).all()

    return proposals


@router.get("/users/me/received-proposals", response_model=List[Proposal])
def get_received_proposals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Get all proposals received on the authenticated user's listings."""
    # Get user from database
    user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
    if not user:
        return []

    # Get proposals on user's trades
    proposals = db.query(ProposalModel).join(
        TradeModel, ProposalModel.trade_id == TradeModel.id
    ).filter(
        TradeModel.creator_user_id == user.id
    ).order_by(ProposalModel.created_at.desc()).all()

    return proposals


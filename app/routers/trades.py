"""Trades router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from nanoid import generate
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.trade import Trade as TradeModel, TradeItem as TradeItemModel
from app.models.card import Card as CardModel
from app.models.user import User as UserModel
from app.models.proposal import TradeProposal as ProposalModel
from app.schemas.trade import TradeCreate, Trade, TradeDetail, TradeItem
from app.schemas.card import Card
from app.schemas.proposal import Proposal
from app.services.feed import compute_quality_score
from app.auth import get_current_user, require_auth
from typing import List

router = APIRouter()


@router.post("/trades", response_model=Trade, status_code=201)
def create_trade(
    trade_data: TradeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Create a new trade post. Requires authentication."""
    # Get or create user in database
    # First try to find by cognito_sub
    user = db.query(UserModel).filter(UserModel.cognito_sub == current_user["sub"]).first()
    if not user:
        # Try to find by email (for existing users without cognito_sub)
        user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
        if user:
            # Update existing user with cognito_sub
            user.cognito_sub = current_user["sub"]
        else:
            # Create new user
            user = UserModel(
                cognito_sub=current_user["sub"],
                handle=current_user["name"] or current_user["email"].split("@")[0],
                email=current_user["email"],
                hashed_password="",  # Not used with Cognito
                is_active=True,
                is_verified=current_user.get("email_verified", False),
            )
            db.add(user)
        db.flush()

    # Generate unique slug
    slug = generate(size=10)

    # Create trade with feed defaults
    trade = TradeModel(
        creator_user_id=user.id,  # Associate with authenticated user
        title=trade_data.title,
        notes=trade_data.notes,
        cash_amount_cents=trade_data.cash_amount_cents,
        share_slug=slug,
        post_type=trade_data.post_type or "TRADE",  # Use provided post_type or default to TRADE
        country="US",
        region="US-East",
        domestic_only=False,
        last_bumped_at=datetime.utcnow(),
    )
    db.add(trade)
    db.flush()  # Get the trade ID

    # Add offered items
    for item_data in trade_data.offered_items:
        item = TradeItemModel(
            trade_id=trade.id,
            side="offer",
            card_id=item_data.card_id,
            qty=item_data.qty,
            condition=item_data.condition,
            language=item_data.language,
            user_photos=item_data.user_photos,
        )
        db.add(item)

    # Add wanted items
    for item_data in trade_data.wanted_items:
        item = TradeItemModel(
            trade_id=trade.id,
            side="want",
            card_id=item_data.card_id,
            qty=item_data.qty,
            condition=item_data.condition,
            language=item_data.language,
            user_photos=item_data.user_photos,
        )
        db.add(item)

    db.flush()  # Flush items so we can access them

    # Set hero_image_url from first offered card
    first_offered = db.query(TradeItemModel).join(CardModel).filter(
        TradeItemModel.trade_id == trade.id,
        TradeItemModel.side == "offer",
        CardModel.image_url.isnot(None)
    ).first()

    if first_offered and first_offered.card:
        trade.hero_image_url = first_offered.card.image_url
    else:
        # Fallback to first wanted card
        first_wanted = db.query(TradeItemModel).join(CardModel).filter(
            TradeItemModel.trade_id == trade.id,
            TradeItemModel.side == "want",
            CardModel.image_url.isnot(None)
        ).first()
        if first_wanted and first_wanted.card:
            trade.hero_image_url = first_wanted.card.image_url

    # Compute quality score
    trade.quality_score = compute_quality_score(trade)

    db.commit()
    db.refresh(trade)

    return trade


@router.get("/trades/{slug}")
def get_trade(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get trade details by slug."""
    trade = db.query(TradeModel).filter(TradeModel.share_slug == slug).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Fetch items with card details
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

    # Get creator info
    creator_user_id = None
    creator_name = None
    if trade.creator:
        creator_user_id = trade.creator.cognito_sub
        creator_name = trade.creator.handle

    # Build response manually to include cognito_sub as creator_user_id
    return {
        "id": str(trade.id),
        "share_slug": trade.share_slug,
        "title": trade.title,
        "notes": trade.notes,
        "cash_amount_cents": trade.cash_amount_cents,
        "creator_user_id": creator_user_id,  # Return cognito_sub instead of database UUID
        "creator_name": creator_name,
        "created_at": trade.created_at.isoformat(),
        "view_count": trade.view_count,
        "status": "active",  # TODO: Add status field to model
        "offered_items": [
            {
                "id": str(item.id),
                "side": item.side,
                "card_id": str(item.card_id),
                "qty": item.qty,
                "condition": item.condition,
                "language": item.language,
                "user_photos": item.user_photos,
                "card": {
                    "id": str(item.card.id),
                    "name": item.card.name,
                    "set_name": item.card.set_name,
                    "card_number": item.card.card_number,
                    "rarity": item.card.rarity,
                    "image_url": item.card.image_url,
                    "game": item.card.game,
                    "external_ids": item.card.external_ids,
                    "created_at": item.card.created_at.isoformat(),
                } if item.card else None
            } for item in offered_items
        ],
        "wanted_items": [
            {
                "id": str(item.id),
                "side": item.side,
                "card_id": str(item.card_id),
                "qty": item.qty,
                "condition": item.condition,
                "language": item.language,
                "user_photos": item.user_photos,
                "card": {
                    "id": str(item.card.id),
                    "name": item.card.name,
                    "set_name": item.card.set_name,
                    "card_number": item.card.card_number,
                    "rarity": item.card.rarity,
                    "image_url": item.card.image_url,
                    "game": item.card.game,
                    "external_ids": item.card.external_ids,
                    "created_at": item.card.created_at.isoformat(),
                } if item.card else None
            } for item in wanted_items
        ]
    }


@router.get("/trades/{slug}/proposals", response_model=List[Proposal])
def get_trade_proposals(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get all proposals for a specific trade."""
    trade = db.query(TradeModel).filter(TradeModel.share_slug == slug).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    proposals = db.query(ProposalModel).filter(
        ProposalModel.trade_id == trade.id
    ).order_by(ProposalModel.created_at.desc()).all()

    return proposals


@router.get("/trades/items/{item_id}/photos")
def get_trade_item_photos(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """Get user photos for a specific trade item (lazy loading)."""
    item = db.query(TradeItemModel).filter(TradeItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Trade item not found")

    return {
        "item_id": str(item.id),
        "user_photos": item.user_photos or []
    }


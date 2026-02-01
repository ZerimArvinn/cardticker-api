"""Trades router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from nanoid import generate

from app.database import get_db
from app.models.trade import Trade as TradeModel, TradeItem as TradeItemModel
from app.schemas.trade import TradeCreate, Trade, TradeDetail, TradeItem
from app.schemas.card import Card

router = APIRouter()


@router.post("/trades", response_model=Trade, status_code=201)
def create_trade(
    trade_data: TradeCreate,
    db: Session = Depends(get_db)
):
    """Create a new trade post."""
    # Generate unique slug
    slug = generate(size=10)
    
    # Create trade
    trade = TradeModel(
        title=trade_data.title,
        notes=trade_data.notes,
        share_slug=slug,
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
        )
        db.add(item)
    
    db.commit()
    db.refresh(trade)
    
    return trade


@router.get("/trades/{slug}", response_model=TradeDetail)
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
    
    # Build response
    trade_detail = TradeDetail.model_validate(trade)
    trade_detail.offered_items = offered_items
    trade_detail.wanted_items = wanted_items
    
    return trade_detail


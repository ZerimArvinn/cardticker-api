"""Feed router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.trade import Trade as TradeModel
from app.schemas.trade import FeedResponse, FeedPost, FeedItemSummary, FeedGeo, TradeItemLite
from app.schemas.card import Card
from app.services.feed import rank_feed_posts

router = APIRouter()


def build_feed_summary(trade: TradeModel) -> FeedItemSummary:
    """Build summary text for feed card."""
    offered_items = [item for item in trade.items if item.side == "offer"]
    wanted_items = [item for item in trade.items if item.side == "want"]
    
    # Build offering text
    if len(offered_items) == 1 and offered_items[0].card:
        offering = f"{offered_items[0].card.name} ({offered_items[0].condition})"
    elif len(offered_items) > 1:
        offering = f"{len(offered_items)} cards"
    else:
        offering = "No items"
    
    # Build requesting text based on post type
    if trade.post_type == "SALE":
        # For SALE, show cash amount
        if trade.cash_amount_cents:
            requesting = f"${trade.cash_amount_cents / 100:.2f}"
        else:
            requesting = "Make offer"
    elif trade.post_type == "WTB":
        # For WTB, show what they're buying
        if len(wanted_items) == 1 and wanted_items[0].card:
            requesting = f"{wanted_items[0].card.name}"
        elif len(wanted_items) > 1:
            requesting = f"{len(wanted_items)} cards"
        else:
            requesting = "Cards"
    else:
        # For TRADE, show wanted items + cash
        parts = []
        if len(wanted_items) == 1 and wanted_items[0].card:
            parts.append(f"{wanted_items[0].card.name}")
        elif len(wanted_items) > 1:
            parts.append(f"{len(wanted_items)} cards")
        
        if trade.cash_amount_cents and trade.cash_amount_cents > 0:
            parts.append(f"${trade.cash_amount_cents / 100:.2f}")
        
        requesting = " + ".join(parts) if parts else "Open to offers"
    
    return FeedItemSummary(offering=offering, requesting=requesting)


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    country: Optional[str] = Query(None, description="Filter by country code (e.g., 'US')"),
    limit: int = Query(20, ge=1, le=50, description="Number of posts to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get ranked feed of trade/sale/WTB posts.
    
    Returns posts ranked by:
    - Recency (50%)
    - Quality/completeness score (40%)
    - Random jitter (10%)
    """
    # Get ranked posts
    posts, total = rank_feed_posts(db, country=country, limit=limit, offset=offset)
    
    # Build feed response
    feed_posts = []
    for trade in posts:
        # Separate offered and wanted items
        offered_items = []
        wanted_items = []
        
        for item in trade.items:
            # Use TradeItemLite to exclude user_photos from feed (performance optimization)
            trade_item = TradeItemLite.model_validate(item)
            if item.card:
                trade_item.card = Card.model_validate(item.card)

            if item.side == "offer":
                offered_items.append(trade_item)
            else:
                wanted_items.append(trade_item)
        
        # Get creator info from the user relationship
        creator_user_id = None
        creator_name = None
        if trade.creator:
            creator_user_id = trade.creator.cognito_sub  # Use cognito_sub instead of database UUID
            creator_name = trade.creator.handle

        # Build feed post
        feed_post = FeedPost(
            post_id=trade.id,
            post_type=trade.post_type,
            share_slug=trade.share_slug,
            created_at=trade.created_at,
            creator_user_id=creator_user_id,
            title=trade.title,
            notes=trade.notes,
            creator_name=creator_name,
            hero_image=trade.hero_image_url,
            summary=build_feed_summary(trade),
            offered_items_count=len(offered_items),
            requested_items_count=len(wanted_items),
            geo=FeedGeo(
                country=trade.country,
                region=trade.region,
                domestic_only=trade.domestic_only
            ),
            quality_score=trade.quality_score,
            offered_items=offered_items,
            requested_items=wanted_items,
            cash_adjustment=trade.cash_amount_cents
        )
        feed_posts.append(feed_post)
    
    return FeedResponse(
        posts=feed_posts,
        total=total,
        has_more=(offset + limit) < total
    )


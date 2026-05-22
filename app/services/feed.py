"""Feed ranking and quality scoring service."""
from sqlalchemy.orm import Session
from app.models.trade import Trade as TradeModel
from typing import Optional


def compute_quality_score(trade: TradeModel) -> int:
    """
    Compute a deterministic quality/completeness score (0-100) for feed ranking.
    
    Based on presence of:
    - Images (hero_image_url)
    - Structured item details (offered/wanted items)
    - Conditions specified
    - Cash component (when applicable)
    - Title and notes
    
    Returns:
        int: Quality score from 0-100
    """
    score = 0
    
    # Hero image present (20 points)
    if trade.hero_image_url:
        score += 20
    
    # Has title (10 points)
    if trade.title and len(trade.title.strip()) > 0:
        score += 10
    
    # Has notes/description (10 points)
    if trade.notes and len(trade.notes.strip()) > 0:
        score += 10
    
    # Count items
    offered_count = sum(1 for item in trade.items if item.side == "offer")
    wanted_count = sum(1 for item in trade.items if item.side == "want")
    
    # Has offered items (20 points)
    if offered_count > 0:
        score += 20
    
    # Has wanted items or is a SALE (20 points)
    # SALE posts don't need wanted items
    if wanted_count > 0 or trade.post_type == "SALE":
        score += 20
    
    # All items have conditions specified (10 points)
    all_have_conditions = all(
        item.condition and item.condition in ["NM", "LP", "MP", "HP", "DMG"]
        for item in trade.items
    )
    if all_have_conditions and len(trade.items) > 0:
        score += 10
    
    # Cash component for SALE/WTB (10 points)
    if trade.post_type in ["SALE", "WTB"] and trade.cash_amount_cents and trade.cash_amount_cents > 0:
        score += 10
    
    return min(100, score)


def rank_feed_posts(
    db: Session,
    country: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[TradeModel], int]:
    """
    Rank and retrieve feed posts using deterministic algorithm.
    
    Ranking factors (v1):
    - Recency (newer = higher)
    - Quality/completeness score
    - Light random jitter (to avoid deterministic ordering ties)
    
    Args:
        db: Database session
        country: Optional country filter (e.g., 'US')
        limit: Number of posts to return
        offset: Pagination offset
    
    Returns:
        tuple: (list of Trade models, total count)
    """
    from sqlalchemy import func, case
    from datetime import datetime, timedelta
    
    # Base query
    query = db.query(TradeModel)
    
    # Apply country filter if specified
    if country:
        query = query.filter(TradeModel.country == country)
    
    # Calculate recency score (0-100)
    # Posts from last 24 hours get 100, decay over 30 days
    now = datetime.utcnow()
    recency_score = case(
        (
            TradeModel.last_bumped_at >= now - timedelta(days=1),
            100
        ),
        (
            TradeModel.last_bumped_at >= now - timedelta(days=7),
            80
        ),
        (
            TradeModel.last_bumped_at >= now - timedelta(days=14),
            60
        ),
        (
            TradeModel.last_bumped_at >= now - timedelta(days=30),
            40
        ),
        else_=20
    )
    
    # Combined ranking score
    # Recency: 50%, Quality: 40%, Random jitter: 10%
    ranking_score = (
        recency_score * 0.5 +
        func.coalesce(TradeModel.quality_score, 50) * 0.4 +
        (func.random() * 10)  # Light jitter to avoid ties
    )
    
    # Get total count
    total = query.count()
    
    # Order by ranking score and paginate
    posts = (
        query
        .order_by(ranking_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return posts, total


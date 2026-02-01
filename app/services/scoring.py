"""Scoring service for trade proposals."""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Tuple
import statistics

from app.models.proposal import TradeProposal
from app.models.price import PricePoint
from app.models.trade import TradeItem
from app.models.proposal import ProposalItem as ProposalItemModel
from app.schemas.proposal import ProposalScores


def get_latest_price(db: Session, card_id: str, condition: str) -> int:
    """Get the latest price for a card in cents."""
    price_point = (
        db.query(PricePoint)
        .filter(
            PricePoint.card_id == card_id,
            PricePoint.condition == condition
        )
        .order_by(desc(PricePoint.ts))
        .first()
    )
    
    if price_point:
        return price_point.price_cents
    
    # Fallback: try NM condition if specific condition not found
    if condition != "NM":
        price_point = (
            db.query(PricePoint)
            .filter(
                PricePoint.card_id == card_id,
                PricePoint.condition == "NM"
            )
            .order_by(desc(PricePoint.ts))
            .first()
        )
        if price_point:
            return price_point.price_cents
    
    return 0  # No price data available


def calculate_total_value(db: Session, items: List) -> int:
    """Calculate total value of items in cents."""
    total = 0
    for item in items:
        price = get_latest_price(db, str(item.card_id), item.condition)
        total += price * item.qty
    return total


def compute_fairness_score(offer_total: int, want_total: int) -> Tuple[int, int, str]:
    """
    Compute fairness score (0-100).
    
    Returns:
        (fairness_score, value_diff_cents, description)
    """
    diff = want_total - offer_total
    diff_abs = abs(diff)
    denom = max(offer_total, want_total, 1)
    
    fairness = max(0, min(100, round(100 - (diff_abs / denom) * 100)))
    
    if diff > 0:
        description = f"Proposer receives ${diff / 100:.2f} more value"
    elif diff < 0:
        description = f"Proposer gives ${abs(diff) / 100:.2f} more value"
    else:
        description = "Trade is perfectly balanced"
    
    return fairness, diff, description


def compute_volatility_score(db: Session, items: List) -> int:
    """
    Compute volatility score (0-100) based on price stability.
    Higher score = more stable prices.
    """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    volatilities = []
    
    for item in items:
        # Get price history for last 30 days
        prices = (
            db.query(PricePoint)
            .filter(
                PricePoint.card_id == item.card_id,
                PricePoint.condition == item.condition,
                PricePoint.ts >= thirty_days_ago
            )
            .order_by(PricePoint.ts)
            .all()
        )
        
        if len(prices) >= 7:  # Need at least 7 data points
            # Calculate daily returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1].price_cents > 0:
                    ret = (prices[i].price_cents - prices[i-1].price_cents) / prices[i-1].price_cents
                    returns.append(ret)
            
            if returns:
                vol = statistics.stdev(returns) if len(returns) > 1 else 0
                volatilities.append(vol)
    
    if not volatilities:
        return 50  # Default score when no data
    
    avg_vol = sum(volatilities) / len(volatilities)
    # Map volatility to score (tune constant as needed)
    vol_score = max(0, min(100, round(100 - (avg_vol * 500))))
    
    return vol_score


def compute_liquidity_score(db: Session, items: List) -> int:
    """
    Compute liquidity score (0-100) based on card popularity.
    Proxy: frequency of card appearances in trades/proposals.
    """
    liquidity_scores = []
    
    for item in items:
        # Count appearances in trade_items
        trade_count = (
            db.query(func.count(TradeItem.id))
            .filter(TradeItem.card_id == item.card_id)
            .scalar()
        )
        
        # Count appearances in proposal_items
        proposal_count = (
            db.query(func.count(ProposalItemModel.id))
            .filter(ProposalItemModel.card_id == item.card_id)
            .scalar()
        )
        
        total_appearances = trade_count + proposal_count
        
        # Log scale for popularity
        import math
        liquidity = math.log(1 + total_appearances)
        liquidity_scores.append(liquidity)
    
    if not liquidity_scores:
        return 50  # Default
    
    # Normalize to 0-100 (simple approach: cap at log(100) ≈ 4.6)
    avg_liquidity = sum(liquidity_scores) / len(liquidity_scores)
    liquidity_score = max(0, min(100, round((avg_liquidity / 4.6) * 100)))
    
    return liquidity_score


def generate_explanation(
    fairness: int,
    volatility: int,
    liquidity: int,
    offer_total: int,
    want_total: int,
    diff: int,
    diff_desc: str
) -> List[str]:
    """Generate human-readable explanation."""
    explanation = []
    
    # Value summary
    explanation.append(
        f"Proposer offers ${offer_total / 100:.2f} worth of cards and wants ${want_total / 100:.2f} in return."
    )
    
    # Fairness
    explanation.append(diff_desc + ".")
    
    if fairness < 70:
        suggestion_amount = abs(diff) / 100
        explanation.append(
            f"Consider adjusting the trade by approximately ${suggestion_amount:.2f} to improve balance."
        )
    
    # Volatility warning
    if volatility < 40:
        explanation.append(
            "Warning: Some cards in this trade have volatile pricing. Values may change significantly."
        )
    
    # Liquidity warning
    if liquidity < 40:
        explanation.append(
            "Note: Some cards may be harder to trade due to lower market activity."
        )
    
    return explanation


def compute_proposal_scores(db: Session, proposal: TradeProposal) -> ProposalScores:
    """Compute all scores for a proposal."""
    # Get proposal items
    offered_items = [item for item in proposal.items if item.side == "offer"]
    wanted_items = [item for item in proposal.items if item.side == "want"]
    
    # Calculate totals
    offer_total = calculate_total_value(db, offered_items)
    want_total = calculate_total_value(db, wanted_items)
    
    # Compute scores
    fairness, diff, diff_desc = compute_fairness_score(offer_total, want_total)
    volatility = compute_volatility_score(db, offered_items + wanted_items)
    liquidity = compute_liquidity_score(db, offered_items + wanted_items)
    
    # Generate explanation
    explanation = generate_explanation(
        fairness, volatility, liquidity,
        offer_total, want_total, diff, diff_desc
    )
    
    return ProposalScores(
        fairness_score=fairness,
        liquidity_score=liquidity,
        volatility_score=volatility,
        proposer_offer_total_cents=offer_total,
        proposer_want_total_cents=want_total,
        value_diff_cents=diff,
        value_diff_description=diff_desc,
        explanation=explanation,
    )


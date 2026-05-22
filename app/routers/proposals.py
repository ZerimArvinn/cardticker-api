"""Proposals router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trade import Trade as TradeModel
from app.models.proposal import TradeProposal as ProposalModel, ProposalItem as ProposalItemModel
from app.models.user import User as UserModel
from app.schemas.proposal import ProposalCreate, Proposal, ProposalDetail, ProposalItem
from app.schemas.card import Card
from app.services.scoring import compute_proposal_scores
from app.auth import require_auth

router = APIRouter()


@router.post("/trades/{slug}/proposals", response_model=Proposal, status_code=201)
def create_proposal(
    slug: str,
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Submit a proposal for a trade. Requires authentication."""
    # Find the trade
    trade = db.query(TradeModel).filter(TradeModel.share_slug == slug).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Get or create user in database
    user = db.query(UserModel).filter(UserModel.email == current_user["email"]).first()
    if not user:
        user = UserModel(
            handle=current_user["name"] or current_user["email"].split("@")[0],
            email=current_user["email"],
            hashed_password="",
            is_active=True,
            is_verified=current_user.get("email_verified", False),
        )
        db.add(user)
        db.flush()

    # Check if user is trying to propose on their own trade
    if trade.creator_user_id and trade.creator_user_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot make a proposal on your own listing")

    # Create proposal
    proposal = ProposalModel(
        trade_id=trade.id,
        proposer_user_id=user.id,  # Associate with authenticated user
        proposer_name=current_user["name"] or current_user["email"],
        cash_amount_cents=proposal_data.cash_amount_cents,
    )
    db.add(proposal)
    db.flush()
    
    # Add offered items
    for item_data in proposal_data.offered_items:
        item = ProposalItemModel(
            proposal_id=proposal.id,
            side="offer",
            card_id=item_data.card_id,
            qty=item_data.qty,
            condition=item_data.condition,
            language=item_data.language,
        )
        db.add(item)
    
    # Add wanted items
    for item_data in proposal_data.wanted_items:
        item = ProposalItemModel(
            proposal_id=proposal.id,
            side="want",
            card_id=item_data.card_id,
            qty=item_data.qty,
            condition=item_data.condition,
            language=item_data.language,
        )
        db.add(item)
    
    db.commit()
    db.refresh(proposal)
    
    return proposal


@router.get("/proposals/{proposal_id}", response_model=ProposalDetail)
def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db)
):
    """Get proposal details with scoring."""
    proposal = db.query(ProposalModel).filter(ProposalModel.id == proposal_id).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Fetch items with card details
    offered_items = []
    wanted_items = []
    
    for item in proposal.items:
        proposal_item = ProposalItem.model_validate(item)
        if item.card:
            proposal_item.card = Card.model_validate(item.card)
        
        if item.side == "offer":
            offered_items.append(proposal_item)
        else:
            wanted_items.append(proposal_item)
    
    # Build response
    proposal_detail = ProposalDetail.model_validate(proposal)
    proposal_detail.offered_items = offered_items
    proposal_detail.wanted_items = wanted_items

    # Add trade slug and creator user ID
    if proposal.trade:
        proposal_detail.trade_slug = proposal.trade.share_slug
        proposal_detail.trade_creator_user_id = proposal.trade.creator_user_id

    # Compute scores
    scores = compute_proposal_scores(db, proposal)
    proposal_detail.scores = scores

    return proposal_detail


@router.post("/proposals/{proposal_id}/mark-viewed")
def mark_proposal_viewed(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Mark a proposal as viewed by the trade creator."""
    from datetime import datetime

    proposal = db.query(ProposalModel).filter(ProposalModel.id == proposal_id).first()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify the current user is the trade creator
    if proposal.trade and proposal.trade.creator:
        if proposal.trade.creator.cognito_sub != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Only the trade creator can mark proposals as viewed")

    # Mark as viewed if not already viewed
    if not proposal.viewed_at:
        proposal.viewed_at = datetime.utcnow()
        db.commit()

    return {"success": True, "viewed_at": proposal.viewed_at}


@router.patch("/proposals/{proposal_id}/accept")
def accept_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Accept a proposal. Only the trade creator can accept."""
    proposal = db.query(ProposalModel).filter(ProposalModel.id == proposal_id).first()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify the current user is the trade creator
    if not proposal.trade or not proposal.trade.creator:
        raise HTTPException(status_code=404, detail="Trade creator not found")

    if proposal.trade.creator.cognito_sub != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Only the trade creator can accept proposals")

    # Check if proposal is already accepted or rejected
    if proposal.status == "accepted":
        raise HTTPException(status_code=400, detail="Proposal is already accepted")

    if proposal.status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot accept a rejected proposal")

    # Update status to accepted
    proposal.status = "accepted"
    db.commit()
    db.refresh(proposal)

    return Proposal.model_validate(proposal)


@router.patch("/proposals/{proposal_id}/reject")
def reject_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Reject a proposal. Only the trade creator can reject."""
    proposal = db.query(ProposalModel).filter(ProposalModel.id == proposal_id).first()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Verify the current user is the trade creator
    if not proposal.trade or not proposal.trade.creator:
        raise HTTPException(status_code=404, detail="Trade creator not found")

    if proposal.trade.creator.cognito_sub != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Only the trade creator can reject proposals")

    # Check if proposal is already accepted or rejected
    if proposal.status == "accepted":
        raise HTTPException(status_code=400, detail="Cannot reject an accepted proposal")

    if proposal.status == "rejected":
        raise HTTPException(status_code=400, detail="Proposal is already rejected")

    # Update status to rejected
    proposal.status = "rejected"
    db.commit()
    db.refresh(proposal)

    return Proposal.model_validate(proposal)


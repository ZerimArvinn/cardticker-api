"""Proposals router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trade import Trade as TradeModel
from app.models.proposal import TradeProposal as ProposalModel, ProposalItem as ProposalItemModel
from app.schemas.proposal import ProposalCreate, Proposal, ProposalDetail, ProposalItem
from app.schemas.card import Card
from app.services.scoring import compute_proposal_scores

router = APIRouter()


@router.post("/trades/{slug}/proposals", response_model=Proposal, status_code=201)
def create_proposal(
    slug: str,
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db)
):
    """Submit a proposal for a trade."""
    # Find the trade
    trade = db.query(TradeModel).filter(TradeModel.share_slug == slug).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Create proposal
    proposal = ProposalModel(
        trade_id=trade.id,
        proposer_name=proposal_data.proposer_name,
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
    
    # Compute scores
    scores = compute_proposal_scores(db, proposal)
    proposal_detail.scores = scores
    
    return proposal_detail


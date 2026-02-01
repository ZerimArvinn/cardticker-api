"""Cards router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.card import Card as CardModel
from app.schemas.card import Card

router = APIRouter()


@router.get("/cards", response_model=List[Card])
def list_cards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all available cards."""
    cards = db.query(CardModel).offset(skip).limit(limit).all()
    return cards


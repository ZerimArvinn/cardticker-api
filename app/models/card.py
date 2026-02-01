"""Card model."""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Card(Base):
    """Pokémon card model."""
    
    __tablename__ = "cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game = Column(String, nullable=False, default="pokemon")
    name = Column(String, nullable=False)
    set_name = Column(String, nullable=False)
    card_number = Column(String, nullable=False)
    rarity = Column(String, nullable=True)
    image_url = Column(Text, nullable=True)
    external_ids = Column(JSONB, nullable=True)  # {"tcgplayer": "123", "ebay": "456"}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


"""Seed script to populate database with sample cards and price data."""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.card import Card
from app.models.price import PricePoint


# Popular Pokémon cards for seeding
SAMPLE_CARDS = [
    {"name": "Charizard ex", "set_name": "Obsidian Flames", "card_number": "125", "rarity": "Double Rare", "base_price": 4500},
    {"name": "Pikachu ex", "set_name": "Paldea Evolved", "card_number": "230", "rarity": "Special Illustration Rare", "base_price": 12000},
    {"name": "Mew ex", "set_name": "151", "card_number": "151", "rarity": "Ultra Rare", "base_price": 8500},
    {"name": "Umbreon VMAX", "set_name": "Evolving Skies", "card_number": "215", "rarity": "Alternate Art", "base_price": 35000},
    {"name": "Rayquaza VMAX", "set_name": "Evolving Skies", "card_number": "218", "rarity": "Alternate Art", "base_price": 28000},
    {"name": "Lugia V", "set_name": "Silver Tempest", "card_number": "186", "rarity": "Full Art", "base_price": 1500},
    {"name": "Giratina VSTAR", "set_name": "Lost Origin", "card_number": "247", "rarity": "Rainbow Rare", "base_price": 4200},
    {"name": "Mewtwo ex", "set_name": "151", "card_number": "163", "rarity": "Special Illustration Rare", "base_price": 15000},
    {"name": "Eevee", "set_name": "151", "card_number": "133", "rarity": "Illustration Rare", "base_price": 2500},
    {"name": "Garchomp ex", "set_name": "Temporal Forces", "card_number": "227", "rarity": "Special Illustration Rare", "base_price": 6500},
    {"name": "Iono", "set_name": "Paldea Evolved", "card_number": "269", "rarity": "Special Illustration Rare", "base_price": 18000},
    {"name": "Professor's Research", "set_name": "Brilliant Stars", "card_number": "159", "rarity": "Full Art", "base_price": 800},
    {"name": "Boss's Orders", "set_name": "Brilliant Stars", "card_number": "157", "rarity": "Full Art", "base_price": 1200},
    {"name": "Miraidon ex", "set_name": "Scarlet & Violet", "card_number": "81", "rarity": "Double Rare", "base_price": 3500},
    {"name": "Koraidon ex", "set_name": "Scarlet & Violet", "card_number": "80", "rarity": "Double Rare", "base_price": 3200},
    {"name": "Gardevoir ex", "set_name": "151", "card_number": "245", "rarity": "Special Illustration Rare", "base_price": 9500},
    {"name": "Alakazam ex", "set_name": "151", "card_number": "200", "rarity": "Ultra Rare", "base_price": 4800},
    {"name": "Gengar ex", "set_name": "151", "card_number": "228", "rarity": "Special Illustration Rare", "base_price": 11000},
    {"name": "Dragonite ex", "set_name": "151", "card_number": "197", "rarity": "Ultra Rare", "base_price": 5200},
    {"name": "Blastoise ex", "set_name": "151", "card_number": "173", "rarity": "Special Illustration Rare", "base_price": 7500},
    {"name": "Venusaur ex", "set_name": "151", "card_number": "172", "rarity": "Special Illustration Rare", "base_price": 7200},
    {"name": "Snorlax", "set_name": "Obsidian Flames", "card_number": "143", "rarity": "Illustration Rare", "base_price": 1800},
    {"name": "Pidgeot ex", "set_name": "Obsidian Flames", "card_number": "164", "rarity": "Ultra Rare", "base_price": 5500},
    {"name": "Charmander", "set_name": "151", "card_number": "004", "rarity": "Common", "base_price": 150},
    {"name": "Squirtle", "set_name": "151", "card_number": "007", "rarity": "Common", "base_price": 150},
    {"name": "Bulbasaur", "set_name": "151", "card_number": "001", "rarity": "Common", "base_price": 150},
    {"name": "Arcanine ex", "set_name": "Obsidian Flames", "card_number": "157", "rarity": "Ultra Rare", "base_price": 4000},
    {"name": "Iron Valiant ex", "set_name": "Paradox Rift", "card_number": "231", "rarity": "Special Illustration Rare", "base_price": 8800},
    {"name": "Roaring Moon ex", "set_name": "Paradox Rift", "card_number": "251", "rarity": "Special Illustration Rare", "base_price": 9200},
    {"name": "Lechonk", "set_name": "Scarlet & Violet", "card_number": "176", "rarity": "Illustration Rare", "base_price": 1200},
]


def generate_price_history(base_price: int, days: int = 30) -> list:
    """Generate realistic price history with some volatility."""
    prices = []
    current_price = base_price
    
    for i in range(days):
        # Add some random walk with mean reversion
        change_pct = random.gauss(0, 0.03)  # 3% daily volatility
        current_price = int(current_price * (1 + change_pct))
        
        # Mean reversion
        if current_price > base_price * 1.2:
            current_price = int(current_price * 0.95)
        elif current_price < base_price * 0.8:
            current_price = int(current_price * 1.05)
        
        prices.append(current_price)
    
    return prices


def seed_database():
    """Seed the database with sample data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Checking for existing data...")
        existing_cards = db.query(Card).count()
        
        if existing_cards > 0:
            print(f"Database already has {existing_cards} cards. Skipping seed.")
            print("To re-seed, drop the database and run again.")
            return
        
        print(f"Seeding {len(SAMPLE_CARDS)} cards...")
        
        # Create cards and price history
        for card_data in SAMPLE_CARDS:
            card = Card(
                game="pokemon",
                name=card_data["name"],
                set_name=card_data["set_name"],
                card_number=card_data["card_number"],
                rarity=card_data.get("rarity"),
            )
            db.add(card)
            db.flush()  # Get the card ID
            
            # Generate 30 days of price history for NM condition
            base_price = card_data["base_price"]
            price_history = generate_price_history(base_price, days=30)
            
            for day_offset, price in enumerate(price_history):
                ts = datetime.utcnow() - timedelta(days=30 - day_offset)
                
                price_point = PricePoint(
                    card_id=card.id,
                    condition="NM",
                    source="seed",
                    price_cents=price,
                    ts=ts,
                )
                db.add(price_point)
            
            # Also add LP condition (slightly lower price)
            for day_offset, price in enumerate(price_history):
                ts = datetime.utcnow() - timedelta(days=30 - day_offset)
                lp_price = int(price * 0.85)  # LP is ~85% of NM
                
                price_point = PricePoint(
                    card_id=card.id,
                    condition="LP",
                    source="seed",
                    price_cents=lp_price,
                    ts=ts,
                )
                db.add(price_point)
            
            print(f"  ✓ {card.name} ({card.set_name})")
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(SAMPLE_CARDS)} cards with 30 days of price history!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()


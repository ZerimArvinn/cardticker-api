"""Seed script to populate the database with diverse trade posts."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.trade import Trade, TradeItem
from app.models.card import Card
from app.models.user import User
import random
from datetime import datetime, timedelta

# Sample trade data
TRADE_TEMPLATES = [
    {
        "title": "Looking to trade my Charizard ex for Pikachu cards!",
        "notes": "Mint condition Charizard ex from Obsidian Flames. Looking for Pikachu ex or vintage Pikachu cards. Open to offers!",
        "post_type": "TRADE",
    },
    {
        "title": "Selling my Mew ex collection - Great prices!",
        "notes": "Near mint condition, pulled fresh from packs. Willing to negotiate on price. Can ship worldwide!",
        "post_type": "SALE",
        "cash_amount_cents": 4500,  # $45
    },
    {
        "title": "WTB: Umbreon VMAX - Paying premium!",
        "notes": "Looking for near mint Umbreon VMAX from Evolving Skies. Will pay above market value for the right card!",
        "post_type": "WTB",
        "cash_amount_cents": 8000,  # $80
    },
    {
        "title": "Trading Rayquaza VMAX + cash for Giratina VSTAR",
        "notes": "Have a beautiful Rayquaza VMAX and willing to add $20 cash for a Giratina VSTAR. Card is in excellent condition!",
        "post_type": "TRADE",
        "cash_amount_cents": 2000,  # $20
    },
    {
        "title": "Eevee collection for trade - Multiple cards available",
        "notes": "Have several Eevee cards from the 151 set. Looking for other eeveelutions or vintage cards. Let's make a deal!",
        "post_type": "TRADE",
    },
    {
        "title": "Lugia V for sale - Mint condition!",
        "notes": "Fresh pull from Silver Tempest. Card went straight into a sleeve. Perfect for collectors!",
        "post_type": "SALE",
        "cash_amount_cents": 3500,  # $35
    },
    {
        "title": "Trading Mewtwo ex for other legendary cards",
        "notes": "Have Mewtwo ex from 151 set. Interested in other legendary Pokemon cards. Show me what you got!",
        "post_type": "TRADE",
    },
    {
        "title": "WTB: Garchomp ex - Need for my collection!",
        "notes": "Looking for Garchomp ex from Temporal Forces. Condition must be NM or better. Paying fair market price!",
        "post_type": "WTB",
        "cash_amount_cents": 2500,  # $25
    },
]

USERNAMES = [
    "PokeMaster2024",
    "CardCollector99",
    "TrainerAsh",
    "PikachuFan",
    "CharizardKing",
    "MewtwoCatcher",
    "EeveeEvolution",
    "DragonTamer",
]

CONDITIONS = ["NM", "LP", "MP"]
REGIONS = ["US-East", "US-West", "US-Central", "EU-West", "Asia-Pacific"]


def seed_trades():
    """Create diverse trade posts in the database."""
    db = SessionLocal()
    
    try:
        # Get all available cards
        cards = db.query(Card).all()
        if not cards:
            print("❌ No cards found in database. Please seed cards first.")
            return
        
        print(f"✅ Found {len(cards)} cards in database")
        
        # Get or create test users
        users = []
        for username in USERNAMES[:len(TRADE_TEMPLATES)]:
            user = db.query(User).filter(User.handle == username).first()
            if not user:
                user = User(
                    handle=username,
                    email=f"{username.lower()}@example.com",
                    hashed_password="dummy_hash_for_seed_data"  # Not used for real auth
                )
                db.add(user)
                db.flush()
            users.append(user)
        
        print(f"✅ Created/found {len(users)} test users")
        
        # Create trades
        created_count = 0
        for i, template in enumerate(TRADE_TEMPLATES):
            # Create trade
            trade = Trade(
                creator_user_id=users[i].id,
                title=template["title"],
                notes=template["notes"],
                post_type=template["post_type"],
                cash_amount_cents=template.get("cash_amount_cents"),
                share_slug=f"trade-{i+1}-{random.randint(1000, 9999)}",
                region=random.choice(REGIONS),
                domestic_only=random.choice([True, False]),
                quality_score=random.randint(70, 100),
                view_count=random.randint(0, 500),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            
            # Add offered items (what they have)
            num_offered = random.randint(1, 3)
            offered_cards = random.sample(cards, min(num_offered, len(cards)))
            for card in offered_cards:
                item = TradeItem(
                    trade_id=trade.id,
                    side="offer",
                    card_id=card.id,
                    qty=random.randint(1, 2),
                    condition=random.choice(CONDITIONS),
                    language="EN",
                )
                trade.items.append(item)
            
            # Add wanted items (what they want) - only for TRADE posts
            if template["post_type"] == "TRADE":
                num_wanted = random.randint(1, 2)
                # Make sure wanted cards are different from offered
                available_wanted = [c for c in cards if c not in offered_cards]
                wanted_cards = random.sample(available_wanted, min(num_wanted, len(available_wanted)))
                for card in wanted_cards:
                    item = TradeItem(
                        trade_id=trade.id,
                        side="want",
                        card_id=card.id,
                        qty=1,
                        condition="NM",
                        language="EN",
                    )
                    trade.items.append(item)
            
            db.add(trade)
            created_count += 1
        
        db.commit()
        print(f"\n🎉 Successfully created {created_count} diverse trade posts!")
        print(f"   - TRADE posts: {sum(1 for t in TRADE_TEMPLATES if t['post_type'] == 'TRADE')}")
        print(f"   - SALE posts: {sum(1 for t in TRADE_TEMPLATES if t['post_type'] == 'SALE')}")
        print(f"   - WTB posts: {sum(1 for t in TRADE_TEMPLATES if t['post_type'] == 'WTB')}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding trades: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Starting trade seed script...\n")
    seed_trades()
    print("\n✅ Seed script complete!")


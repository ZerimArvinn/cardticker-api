# Quick Start Guide

## 1. Start PostgreSQL

```bash
docker-compose up -d
```

Wait a few seconds for PostgreSQL to be ready.

## 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Run Database Migrations

```bash
alembic upgrade head
```

## 4. Seed the Database

```bash
python scripts/seed.py
```

This will create 30 popular Pokémon cards with 30 days of price history.

## 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

## 6. Test the API

Open http://localhost:8000/docs in your browser to see the interactive API documentation.

### Example: Create a Trade

```bash
curl -X POST http://localhost:8000/api/trades \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Looking for Charizard",
    "offered_items": [
      {"card_id": "<CARD_ID>", "qty": 1, "condition": "NM"}
    ],
    "wanted_items": [
      {"card_id": "<CARD_ID>", "qty": 1, "condition": "NM"}
    ]
  }'
```

First, get card IDs from: http://localhost:8000/api/cards

## Running Tests

```bash
pytest
```

## Troubleshooting

### Database Connection Error

Make sure PostgreSQL is running:
```bash
docker-compose ps
```

### Port Already in Use

Change the port:
```bash
uvicorn app.main:app --reload --port 8001
```


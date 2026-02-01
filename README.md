# CardTicker Trades API

Backend API for CardTicker Trades - a trade-link + AI trade scoring platform for Pokémon card trading.

## Overview

This FastAPI backend provides structured trade links and objective scoring. Users create Trade Posts, share links, and receive Trade Proposals with automated fairness, liquidity, and volatility scoring.

## Features

- ✅ Trade Post creation and management
- ✅ Trade Proposal submission with scoring
- ✅ Fairness, liquidity, and volatility scoring algorithms
- ✅ Cached pricing with seed data
- ✅ RESTful API with automatic OpenAPI docs

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Validation**: Pydantic v2

## Project Structure

```
cardticker-api/
├── app/
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── routers/      # API endpoints
│   ├── services/     # Business logic (scoring)
│   ├── database.py   # DB connection
│   └── main.py       # FastAPI app
├── alembic/          # Database migrations
├── scripts/          # Seed scripts
├── tests/            # Tests
├── db/               # Database init scripts
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker Desktop (includes Docker Compose)

### 1. Start Everything

```bash
docker compose up --build -d
```

This starts both PostgreSQL and the FastAPI application in Docker containers.

### 2. Run Database Migrations

```bash
docker exec cardticker-trades-api alembic revision --autogenerate -m "Initial schema"
docker exec cardticker-trades-api alembic upgrade head
```

### 3. Seed the Database

```bash
docker exec cardticker-trades-api python scripts/seed.py
```

This creates 30 popular Pokémon cards with 30 days of price history.

### 4. Access the API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Commands

### View Logs
```bash
docker compose logs -f api
docker compose logs -f postgres
```

### Stop Everything
```bash
docker compose down
```

### Stop and Remove Data
```bash
docker compose down -v
```

### Restart API (after code changes)
The API runs with hot-reload enabled, so changes are automatically reflected.
```bash
docker compose restart api
```

### Run Commands Inside Container
```bash
# Python shell
docker exec -it cardticker-trades-api python

# Bash shell
docker exec -it cardticker-trades-api bash

# Access database
docker exec -it cardticker-trades-db psql -U cardticker -d cardticker_trades
```

## API Endpoints

### Cards
- `GET /api/cards` - List all available cards

### Trades
- `POST /api/trades` - Create a trade post
- `GET /api/trades/{slug}` - Get trade post details

### Proposals
- `POST /api/trades/{slug}/proposals` - Submit a proposal
- `GET /api/proposals/{proposal_id}` - Get proposal with scores

## Scoring System

### Fairness Score (0-100)
Measures value balance between both sides of the trade.

### Liquidity Score (0-100)
Proxy based on card popularity and trade frequency.

### Volatility Score (0-100)
Based on price stability over the last 30 days.

## Development

The API runs with hot-reload enabled, so code changes are automatically reflected.

### Database Migrations

```bash
# Create a new migration
docker exec cardticker-trades-api alembic revision --autogenerate -m "description"

# Apply migrations
docker exec cardticker-trades-api alembic upgrade head

# Rollback
docker exec cardticker-trades-api alembic downgrade -1
```

### Running Tests

```bash
docker exec cardticker-trades-api pytest
```

## Next Steps

Build the Next.js frontend in the `cardticker` repository to create the user interface for:
- Creating trade posts (`/t/new`)
- Viewing trades (`/t/[slug]`)
- Submitting proposals (`/t/[slug]/propose`)
- Viewing proposal scores (`/p/[id]`)

## License

MIT
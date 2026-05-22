"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import trades, proposals, cards, feed, users

app = FastAPI(
    title="CardTicker Trades API",
    description="API for Pokémon card trading with AI-powered scoring",
    version="1.0.0",
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://192.168.1.174:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trades.router, prefix="/api", tags=["trades"])
app.include_router(proposals.router, prefix="/api", tags=["proposals"])
app.include_router(cards.router, prefix="/api", tags=["cards"])
app.include_router(feed.router, prefix="/api", tags=["feed"])
app.include_router(users.router, prefix="/api", tags=["users"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CardTicker Trades API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


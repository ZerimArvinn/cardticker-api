#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
sleep 2

echo "Running Alembic migrations..."
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

echo "Seeding database..."
python scripts/seed.py

echo "✅ Database initialized successfully!"


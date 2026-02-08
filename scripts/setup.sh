#!/bin/bash
set -e

echo "=== SimplePageGenerator Setup ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "PostgreSQL is required but not installed."; exit 1; }

cd "$(dirname "$0")/.."

# Create .env from example if missing
if [ ! -f backend/.env ]; then
  cp .env.example backend/.env
  echo "Created backend/.env from .env.example - please update with your settings"
fi

# Setup backend
echo "Setting up backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Create database if it doesn't exist
echo "Setting up database..."
createdb simplepagegen 2>/dev/null || echo "Database 'simplepagegen' already exists"

# Run migrations
alembic upgrade head

cd ..

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "=== Setup complete! ==="
echo "1. Edit backend/.env with your OPENAI_API_KEY"
echo "2. Run: ./scripts/dev.sh"

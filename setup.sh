#!/bin/bash
# setup.sh — scaffold the initial folder structure and config files for order-sync-engine
# Run this from inside the order-sync-engine folder (after git init)

set -e  # stop on error

echo "Creating folder structure..."
mkdir -p src/db/migrations
mkdir -p src/integrations
mkdir -p src/validation
mkdir -p src/sync
mkdir -p tests
mkdir -p docs

echo "Creating __init__.py files (so Python treats these as packages)..."
touch src/__init__.py
touch src/db/__init__.py
touch src/integrations/__init__.py
touch src/validation/__init__.py
touch src/sync/__init__.py
touch tests/__init__.py

echo "Creating .env.example..."
cat > .env.example << 'ENVEOF'
# Copy this file to .env and fill in your real values
# DO NOT commit .env to git

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/order_sync

# Shopify Admin API (Client Credentials Grant)
SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
SHOPIFY_CLIENT_ID=
SHOPIFY_CLIENT_SECRET=
SHOPIFY_ACCESS_TOKEN=

# Sync settings
SYNC_INTERVAL_MINUTES=15
ENVEOF

echo "Creating .gitignore..."
cat > .gitignore << 'GITEOF'
# Environment & secrets
.env
credentials.json
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.eggs/
venv/
env/
.venv/

# Database
*.db
*.sqlite3

# IDE / editor
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Docker
docker-compose.override.yml
GITEOF

echo "Creating requirements.txt..."
cat > requirements.txt << 'REQEOF'
# Database
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9

# HTTP client (for calling the Shopify API)
requests==2.32.3

# Scheduler
apscheduler==3.10.4

# Environment variables
python-dotenv==1.0.1

# Testing
pytest==8.3.3
pytest-mock==3.14.0
REQEOF

echo "Creating docker-compose.yml (local Postgres for development)..."
cat > docker-compose.yml << 'DCEOF'
services:
  postgres:
    image: postgres:16
    container_name: order_sync_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: order_sync
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
DCEOF

echo ""
echo "Done! Files created:"
echo ""
find . -type f -not -path './.git/*' | sort

echo ""
echo "Next steps:"
echo "1. Review .env.example, then copy it to .env: cp .env.example .env"
echo "2. Create a virtual environment: python -m venv .venv"
echo "3. Activate it: source .venv/Scripts/activate"
echo "4. Install dependencies: pip install -r requirements.txt"

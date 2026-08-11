#!/bin/bash
# setup.sh — bikin struktur folder + file awal untuk order-sync-engine
# Jalankan ini dari dalam folder order-sync-engine (setelah git init)

set -e  # stop kalau ada error

echo "Membuat struktur folder..."
mkdir -p src/db/migrations
mkdir -p src/integrations
mkdir -p src/validation
mkdir -p src/sync
mkdir -p tests
mkdir -p docs

echo "Membuat file __init__.py (biar Python kenali folder ini sebagai package)..."
touch src/__init__.py
touch src/db/__init__.py
touch src/integrations/__init__.py
touch src/validation/__init__.py
touch src/sync/__init__.py
touch tests/__init__.py

echo "Membuat .env.example..."
cat > .env.example << 'EOF'
# Salin file ini jadi .env dan isi dengan value asli kamu
# JANGAN commit file .env ke git

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/order_sync

# Shopify (isi setelah bikin development store)
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=

# Google Sheets (isi belakangan)
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEET_ID=

# Sync settings
SYNC_INTERVAL_MINUTES=15
EOF

echo "Membuat .gitignore..."
cat > .gitignore << 'EOF'
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

# Virtual environment (kalau kamu bikin di dalam folder proyek)
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
EOF

echo "Membuat requirements.txt..."
cat > requirements.txt << 'EOF'
# Database
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9

# HTTP client (buat panggil Shopify API)
requests==2.32.3

# Scheduler
apscheduler==3.10.4

# Environment variables
python-dotenv==1.0.1

# Google Sheets (dipakai belakangan)
gspread==6.1.4
google-auth==2.35.0

# Testing
pytest==8.3.3
pytest-mock==3.14.0
EOF

echo "Membuat docker-compose.yml (Postgres lokal buat development)..."
cat > docker-compose.yml << 'EOF'
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
EOF

echo ""
echo "Selesai! Struktur folder yang dibuat:"
echo ""
find . -type f -not -path './.git/*' | sort

echo ""
echo "Langkah selanjutnya:"
echo "1. Review isi .env.example, lalu copy jadi .env: cp .env.example .env"
echo "2. Bikin virtual environment: python -m venv .venv"
echo "3. Aktifkan venv: source .venv/Scripts/activate"
echo "4. Install dependencies: pip install -r requirements.txt"

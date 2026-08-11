# Order Sync Engine

A reliable, automated pipeline that pulls orders from Shopify, validates them, and stores them in PostgreSQL — with idempotency, retry logic, and scheduled execution built in.

## The Problem

Small and medium e-commerce businesses often rely on manual exports or fragile scripts to move order data from their storefront into a database or reporting tool. This leads to:

- **Duplicate or missing orders** when a sync is re-run or interrupted
- **Bad data reaching the database** with no validation layer in front of it
- **No visibility** when a sync silently fails

**Order Sync Engine** solves this with a small production-style pipeline: fetch → validate → save, safely and repeatably, on a schedule — with a quarantine table for anything that fails validation, and a log of every sync run.

## Architecture

```
Shopify Admin API (orders)
        │
        ▼
  fetch_orders()  ──── retry_with_backoff: 4 attempts, 1s → 2s → 4s → 8s
        │
        ▼
  validate_order()  ── invalid → quarantine table (with failure_reason)
        │
        ▼
   orders table   ◄──── idempotent upsert (matched on shopify_order_id)
        │
        ▼
   sync_log table  ──── every run logged: fetched / synced / quarantined / status

Triggered by: scheduler.py (APScheduler, runs every SYNC_INTERVAL_MINUTES)
```

## Key Features

- **Idempotent syncing** — orders are matched on `shopify_order_id`; re-running a sync updates existing rows instead of duplicating them
- **Validation before storage** — required fields, positive quantity/price, and valid SKU are checked before anything touches the `orders` table
- **Quarantine, not discard** — records that fail validation are kept in a separate `quarantine` table with a human-readable `failure_reason`, so nothing is silently lost
- **Automatic retries** — Shopify API calls are wrapped in exponential backoff (4 attempts) to absorb transient network/API failures
- **Scheduled execution** — `scheduler.py` runs the sync unattended on a fixed interval, and keeps retrying on the next cycle if a run fails
- **Full audit trail** — every run (success, partial, or failed) is recorded in `sync_log` with record counts and error messages
- **Tested** — validation logic covered by pytest unit tests, isolated from the database and API

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic |
| Source API | Shopify Admin API (Client Credentials Grant) |
| Scheduling | APScheduler |
| Testing | pytest |
| Environment | Docker Compose (Postgres) |

## Database Schema

- **`orders`** — validated orders, upserted by `shopify_order_id` (`customer_name`, `sku`, `quantity`, `price`, `status`, `raw_payload`, timestamps)
- **`quarantine`** — orders that failed validation, kept with `failure_reason` and a `reviewed` flag for manual follow-up
- **`sync_log`** — one row per sync run: `orders_fetched`, `orders_synced`, `orders_quarantined`, `status`, `error_message`

## Getting Started

```bash
# Clone the repo
git clone https://github.com/ajiautomation/order-sync-engine.git
cd order-sync-engine

# Start PostgreSQL
docker compose up -d

# Set up a virtual environment
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Fill in SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN in .env

# Run database migrations
alembic upgrade head

# Run a single sync
python -m src.sync.sync_engine

# Or run the scheduler (repeats every SYNC_INTERVAL_MINUTES)
python -m src.scheduler
```

## Running Tests

```bash
pytest
```

## Roadmap

- [ ] Google Sheets sync — mirror synced orders to a live spreadsheet for non-technical stakeholders
- [ ] Webhook-driven variant — replace polling with real-time Shopify webhooks + error recovery (next portfolio project)

---

*Part of a freelance portfolio focused on API integration, data pipeline automation, and backend reliability.*

"""
SQLAlchemy models — definisi struktur tabel database.
Alembic membaca file ini untuk tahu struktur tabel apa yang seharusnya ada.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    JSON,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    """Order yang lolos validasi — data bersih siap dipakai."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    shopify_order_id = Column(String, unique=True, nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    status = Column(String, nullable=False, default="synced")
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Quarantine(Base):
    """Order yang gagal validasi — disimpan untuk direview manual, bukan dibuang."""

    __tablename__ = "quarantine"

    id = Column(Integer, primary_key=True)
    shopify_order_id = Column(String, nullable=False, index=True)
    raw_payload = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=False)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SyncLog(Base):
    """Audit trail — catatan setiap kali proses sync dijalankan."""

    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True)
    run_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    orders_fetched = Column(Integer, default=0)
    orders_synced = Column(Integer, default=0)
    orders_quarantined = Column(Integer, default=0)
    status = Column(String, nullable=False)  # 'success' | 'failed' | 'partial'
    error_message = Column(Text, nullable=True)

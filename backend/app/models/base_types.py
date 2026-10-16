"""
ARGUS — Database-agnostic column types.
Uses PostgreSQL-native types when available, falls back to generic
types for SQLite (used in tests).
"""

import os
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy import types

# Detect if we're using SQLite (test environment)
_db_url = os.environ.get("DATABASE_URL", "")
_is_sqlite = "sqlite" in _db_url


class SmartJSON(types.TypeDecorator):
    """JSONB on PostgreSQL, JSON on SQLite."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class SmartUUID(types.TypeDecorator):
    """UUID on PostgreSQL, String(36) on SQLite."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import uuid
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

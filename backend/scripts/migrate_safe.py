"""
ARGUS — Safe migration helper.

If the database already has tables from Phase 1 (create_all),
this script stamps the current state as the migration head
instead of trying to re-create everything.

Usage:
    cd backend
    .venv\\Scripts\\python.exe -m scripts.migrate_safe
"""

import asyncio
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


async def count_existing_tables() -> int:
    try:
        import asyncpg
        from app.core.config import settings
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        await conn.close()
        return len(rows)
    except Exception as e:
        print(f"Could not connect to database: {e}")
        return -1


async def check_alembic_version() -> bool:
    """Return True if alembic_version table exists and has a row."""
    try:
        import asyncpg
        from app.core.config import settings
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch("SELECT version_num FROM alembic_version")
            await conn.close()
            return len(rows) > 0
        except Exception:
            await conn.close()
            return False
    except Exception:
        return False


def run_alembic(*args):
    venv_alembic = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "alembic.exe")
    if not os.path.exists(venv_alembic):
        venv_alembic = "alembic"
    result = subprocess.run([venv_alembic] + list(args), cwd=os.path.join(os.path.dirname(__file__), ".."))
    return result.returncode


async def main():
    print("ARGUS — Safe Migration Helper")
    print("=" * 40)

    has_alembic_version = await check_alembic_version()
    if has_alembic_version:
        print("✓ Alembic version table exists — checking current head…")
        code = run_alembic("current")
        if code == 0:
            print("✓ Database is already tracked by Alembic.")
            print("  To apply new migrations: alembic upgrade head")
            return

    table_count = await count_existing_tables()
    print(f"Found {table_count} tables in the public schema.")

    if table_count >= 10:
        print("\nDatabase already has tables from Phase 1 (create_all).")
        print("Stamping as migration head to avoid re-creation…")
        code = run_alembic("stamp", "head")
        if code == 0:
            print("✓ Stamped successfully. Future migrations will apply incrementally.")
        else:
            print("✗ Stamp failed. Check alembic.ini and database connection.")
    elif table_count >= 0:
        print("\nDatabase appears empty or has few tables.")
        print("Running initial migration…")
        code = run_alembic("upgrade", "head")
        if code == 0:
            print("✓ Initial migration applied successfully.")
        else:
            print("✗ Migration failed. Check alembic.ini and DATABASE_URL.")
    else:
        print("✗ Could not connect to database. Check DATABASE_URL in .env")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

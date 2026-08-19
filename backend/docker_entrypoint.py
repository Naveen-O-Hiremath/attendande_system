"""Container startup sequence: wait for the database, migrate, seed, serve.

A plain shell entrypoint script is a classic source of cross-platform pain
(CRLF line endings from a Windows checkout break the shebang, the
executable bit gets lost on some bind-mount setups) so this is Python
instead - invoked as `python docker_entrypoint.py`, which sidesteps all of
that.
"""

import asyncio
import os
import subprocess
import sys
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def wait_for_db(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    print("Waiting for the database to accept connections...")
    engine = create_async_engine(settings.DATABASE_URL)
    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("  database is ready.")
            return
        except Exception as exc:  # noqa: BLE001 - intentionally broad: retry on any connection failure
            print(f"  ({attempt}/{max_attempts}) not ready yet: {exc}")
            time.sleep(delay_seconds)
    sys.exit("Database did not become ready in time.")


def run_migrations() -> None:
    print("Running database migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def seed_admin() -> None:
    print("Seeding default admin account (idempotent)...")
    subprocess.run([sys.executable, "-m", "app.seed"], check=True)


def main() -> None:
    asyncio.run(wait_for_db())
    run_migrations()
    seed_admin()
    print("Starting API server...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()

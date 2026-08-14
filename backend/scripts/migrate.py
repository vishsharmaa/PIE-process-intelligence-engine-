#!/usr/bin/env python3
"""Helper script to run alembic migrations."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command

if __name__ == "__main__":
    ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")
    cfg = Config(ini_path)
    print("Running database migrations (alembic upgrade head)...")
    command.upgrade(cfg, "head")
    print("✓ Migrations completed successfully!")

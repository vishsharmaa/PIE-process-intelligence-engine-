from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db import Base
from app import models  # noqa: ensure models are registered
from dotenv import load_dotenv
load_dotenv()

config = context.config
if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://pie:pie@localhost:5432/pie")
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=db_url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section),
                                     prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel
from services.document_api.app.models.user import *  # import all your models here
import os
# this is the Alembic Config object
config = context.config

# set up logging
fileConfig(config.config_file_name)

# point to your SQLModel metadata
target_metadata = SQLModel.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {
            **config.get_section(config.config_ini_section),
            "sqlalchemy.url": os.getenv(
                "SYNC_DATABASE_URL",
                config.get_main_option("sqlalchemy.url"),
            ),
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic.config import Config
from alembic import command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migrations():
    """Run database migrations using Alembic."""
    try:
        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Get the project root directory (parent of app directory)
        project_root = os.path.dirname(current_dir)
        
        # Create Alembic configuration
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        print('alembic_cfg', alembic_cfg)
        
        # Use DATABASE_URL from environment if available, otherwise use the one in alembic.ini
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # For Railway, adapt the URL if it's PostgreSQL async URL
            if db_url.startswith("postgresql+asyncpg://"):
                sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)
            else:
                alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        logger.info("Starting database migration...")
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running database migrations: {str(e)}")
        # In development, we raise the exception to see the error
        # In production, we might want to continue despite migration errors
        if os.getenv("DEBUG", "").lower() in ("true", "1", "t"):
            raise
        else:
            logger.error("Application will continue despite migration error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    debug_mode = os.getenv("DEBUG", "").lower() in ("true", "1", "t")
    
    # We always run migrations but log differently based on environment
    if debug_mode:
        logger.info("Running migrations in development mode...")
    else:
        logger.info("Running migrations in production mode...")
    
    await run_migrations()
    
    yield
    
    # Cleanup (if needed) happens after the yield 
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

# Load .env variables
load_dotenv()

# Use async Postgres connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Ensure URL is prefixed correctly for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"Using ASYNC DATABASE_URL: {DATABASE_URL}")

# Create async SQLAlchemy engine
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True,
    connect_args={"ssl": False}  # ← force plain connection for asyncpg

)

# Create async session factory
async_sessionmaker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Alias for compatibility
async_session = async_sessionmaker

# Base class for async ORM models
Base = declarative_base()

# Async dependency for FastAPI routes (if needed)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker() as session:
        yield session


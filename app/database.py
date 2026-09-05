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

# Log where we are pointed, without leaking the password into Fly's logs.
def _mask_password(url: str) -> str:
    """Hide the password so startup logs can be shared without leaking it."""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, host = rest.rsplit("@", 1)
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host}"


_safe_url = _mask_password(DATABASE_URL)
print(f"Using ASYNC DATABASE_URL: {_safe_url}")

# SQL_ECHO=1 turns statement logging back on for local debugging. It stays off
# by default: echoing every statement in production is pure latency and noise.
SQL_ECHO = os.getenv("SQL_ECHO", "").lower() in ("1", "true", "yes")

# Create async SQLAlchemy engine.
#
# The app runs in dfw and Postgres in sjc, so connections cross regions and get
# dropped if they sit around. pool_pre_ping only catches a connection that is
# already dead before we use it -- pool_recycle is what stops us holding one
# long enough to be killed mid-query ("connection was closed in the middle of
# operation"). The pool is deliberately small: two machines x these limits is
# what the database actually sees.
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # discard connections that died while idle
    pool_recycle=300,        # never reuse one older than 5 minutes
    pool_size=5,
    max_overflow=5,          # hard ceiling of 10 per machine
    pool_timeout=10,         # fail fast rather than queueing for 30s
    echo=SQL_ECHO,
    connect_args={"ssl": False},  # plain connection over Fly's private network
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


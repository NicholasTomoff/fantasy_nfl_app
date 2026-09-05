import os
import json
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from traceback import format_exc
import asyncio
from sqlalchemy.exc import OperationalError

from app.database import Base, async_engine, async_sessionmaker
from app.models import Player

from app.routes.teams import router as teams_router
from app.routes.players import router as players_router
from app.routes.picks import router as picks_router
from app.routes.weeklyplayerhits import router as weeklyplayerhits_router
from app.routes import users, scoring, leagues
from app.routes.standings import router as standings_router
from app.routes.ranks import router as ranks_router
from app.routes.invites import router as invites_router
from app.routes.seasons import router as seasons_router
from app.routes.weeks import router as weeks_router
from app.routes import admin

# Set up logging early
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn.error")

load_dotenv()

async def create_all_tables_async(retries=5, delay=2):
    for attempt in range(retries):
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Tables created")
            return
        except OperationalError as e:
            print(f"⚠️ DB connection failed (attempt {attempt+1}/{retries}): {e}")
            await asyncio.sleep(delay)
    raise RuntimeError("❌ Could not connect to the database after several retries.")

async def seed_players_async():
    async with async_sessionmaker() as session:
        result = await session.execute(
            Player.__table__.select().limit(1)
        )
        if result.first():
            logger.debug("Players already seeded.")
            return

        data_path = os.path.join(os.path.dirname(__file__), "data", "players_2024.json")
        logger.debug(f"Seeding players from {data_path}")
        with open(data_path, "r") as f:
            players_data = json.load(f)
            for p in players_data:
                p.pop("team_name", None)
                session.add(Player(**p))
        await session.commit()
        logger.debug("Finished seeding players.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("🔄 Starting application lifespan...")
    try:
        await create_all_tables_async()
        logger.debug("✅ Tables created successfully.")
        await seed_players_async()
        logger.debug("✅ Players seeded successfully.")
    except Exception as e:
        logger.exception(f"❌ Error during startup: {e}")
        logger.error(format_exc())  # ← ADD THIS to see full traceback
        raise
    yield
    logger.debug("🛑 Application shutdown complete.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Fantasy NFL API is running!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://triple-streak-frontend.onrender.com",
        "https://fantasy-nfl-app.fly.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(teams_router, prefix="/api", tags=["teams"])
app.include_router(players_router, prefix="/api", tags=["players"])
app.include_router(picks_router, prefix="/api", tags=["picks"])
app.include_router(weeklyplayerhits_router, prefix="/api/weeklyplayerhits", tags=["weeklyplayerhits"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(scoring.router)
app.include_router(standings_router, prefix="/api", tags=["standings"])
app.include_router(leagues.router)
app.include_router(ranks_router, prefix="/api/user", tags=["user"])
app.include_router(invites_router, prefix="/api/invites", tags=["invites"])
app.include_router(seasons_router, prefix="/api/seasons", tags=["seasons"])
app.include_router(weeks_router, prefix="/api/weeks", tags=["weeks"])
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    print("Starting on host:", os.getenv("HOST", "0.0.0.0"))
    print("Starting on port:", os.getenv("PORT", "8080"))
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


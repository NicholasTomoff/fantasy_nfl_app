from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db  # async session dependency
from app.models import Team
from app.schemas import TeamOut
from app.nfl_api_client import NFLAPIClient
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("RAPIDAPI_KEY")
if not api_key:
    raise ValueError("Missing RAPIDAPI_KEY in environment variables")

router = APIRouter()
client = NFLAPIClient(api_key=api_key)

# --------- Get All Players Info ---------
@router.get("/nfl/players")
async def players():
    # Assuming NFLAPIClient.get_players is sync; run in threadpool to avoid blocking
    from fastapi.concurrency import run_in_threadpool
    players_data = await run_in_threadpool(client.get_players)
    return {"players": players_data}

# --------- Get All Team Info ---------
@router.get("/nfl/teams", response_model=list[TeamOut])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    return teams

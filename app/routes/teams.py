from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Team
from app.schemas import TeamOut

router = APIRouter()

# Get NFL teams info
@router.get("/teams", response_model=list[TeamOut])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    return teams

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from services.ranking import get_user_ranks
from app.auth import get_current_user

router = APIRouter()

# GET user ranks; global across all leagues, league rank, and current triple streak count
@router.get("/ranks")
async def user_ranks(
    league_id: int = Query(..., description="League ID to get ranks for"),
    week: int = Query(..., description="Week to calculate ranks for"),
    season: int = Query(..., description="NFL season year"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    print(f"[DEBUG] /ranks endpoint called with league_id={league_id}, week={week}, season={season}, user={current_user.email}")

    user_email = current_user.email
    if not user_email:
        raise HTTPException(status_code=400, detail="User email not found")

    try:
        ranks = await get_user_ranks(db, user_email=user_email, league_id=league_id, week=week, season=season)
    except Exception as e:
        print(f"[ERROR] Exception in get_user_ranks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user ranks")

    print(f"[DEBUG] Ranks returned: {ranks}")
    return ranks

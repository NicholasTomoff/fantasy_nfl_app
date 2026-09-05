from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
from sqlalchemy import select

from app import models, schemas
from app.database import get_db

router = APIRouter()

# Get positional pick success (hit) for user in league, season, and current week
@router.get("/user/{user_email}/league/{league_id}/season/{season}/week/{week}", response_model=schemas.WeeklyScoreRead, )
async def get_weekly_player_hits_for_week(
    user_email: str,
    league_id: int,
    season: int,
    week: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = select(models.WeeklyScore).where(
            (models.WeeklyScore.user_email == user_email),
            (models.WeeklyScore.league_id == league_id),
            (models.WeeklyScore.season == season),
            (models.WeeklyScore.week == week),
        )
        result = await db.execute(stmt)
        score = result.scalars().first()

        if not score:
            return schemas.WeeklyScoreRead(
                id=0,
                user_email=user_email,
                league_id=league_id,
                season=season,
                week=week,
                qb_points=0,
                rb_points=0,
                wr_points=0,
                qb_streak=0,
                rb_streak=0,
                wr_streak=0,
                all_positions_hit=False,
                all_positions_bonus=0,
                total_points=0,
                created_at=datetime.utcnow(),
            )
        return score

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {str(e)}"},
        )

# Get positional pick success (hit) for all users in league, season, and current week
@router.get("/league/{league_id}/season/{season}/week/{week}", response_model=List[schemas.WeeklyScoreRead],)
async def get_weekly_league_hits_for_week(league_id: int, season: int, week: int, db: AsyncSession = Depends(get_db),):
    try:
        stmt = select(models.WeeklyScore).where(
            (models.WeeklyScore.league_id == league_id),
            (models.WeeklyScore.season == season),
            (models.WeeklyScore.week == week),
        )
        result = await db.execute(stmt)
        scores = result.scalars().all()
        return scores

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal server error: {str(e)}"},
        )

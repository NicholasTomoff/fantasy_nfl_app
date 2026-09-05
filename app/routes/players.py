import traceback
import logging
from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased

from app.database import get_db
from app import models, schemas
from app.models import WeeklyPick, Player, PlayerGameStat, WeeklyScore, NFLGame, Team

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

# ---------- Endpoint 1: Get players by position ----------
@router.get("/players/{position}", response_model=List[schemas.PlayerOut])
async def get_players_by_position(position: str, db: AsyncSession = Depends(get_db)):
    stmt = select(models.Player).options(joinedload(models.Player.team))
    
    if position.upper() == "WR":
        stmt = stmt.filter(models.Player.position.in_(["WR", "TE"]))
    else:
        stmt = stmt.filter(models.Player.position == position.upper())

    result = await db.execute(stmt)
    return result.scalars().all()

# ---------- Endpoint 2: Get top players by position ----------
@router.get("/top_players/{position}")
async def get_top_players_by_position(position: str, season: int = Query(..., description="NFL season year"), db: AsyncSession = Depends(get_db)):
    position_upper = position.upper()

    stat_field = {
        "QB": PlayerGameStat.passing_yards,
        "RB": PlayerGameStat.rushing_yards,
        "WR": PlayerGameStat.receiving_yards,
    }.get(position_upper)

    if not stat_field:
        raise HTTPException(status_code=400, detail="Invalid position")

    pg = aliased(PlayerGameStat)
    g = aliased(NFLGame)

    stmt = (
        select(
            Player.player_id,
            Player.player_name,
            Player.team_name,
            Player.team_id,
            func.coalesce(func.sum(
                pg.passing_yards if position_upper == "QB" 
                else pg.rushing_yards if position_upper == "RB" 
                else pg.receiving_yards
            ), 0).label("total_yards"),
        )
        .outerjoin(pg, Player.player_id == pg.player_id)
        .outerjoin(g, (pg.game_id == g.id) & (g.season == season))
    )

    if position_upper == "WR":
        stmt = stmt.filter(Player.position.in_(["WR", "TE"]))
    else:
        stmt = stmt.filter(Player.position == position_upper)

    stmt = (
        stmt.filter(Player.active == True)
        .filter(g.season == season)  # ✅ apply season filter AFTER the join
        .group_by(Player.player_id, Player.player_name, Player.team_name, Player.team_id)
        .order_by(func.coalesce(func.sum(
            pg.passing_yards if position_upper == "QB" 
            else pg.rushing_yards if position_upper == "RB" 
            else pg.receiving_yards
        ), 0).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "player_id": r.player_id,
            "player_name": r.player_name,
            "team_name": r.team_name,
            "team_id": r.team_id,
            "total_yards": r.total_yards or 0,
        }
        for r in rows
    ]

# ---------- Endpoint 3: Get restricted players on streak or game start time passed ----------
@router.get("/restricted_players/{user_email}")
async def get_restricted_players(user_email: str, week: int = Query(...), league_id: int = Query(...), season: int = Query(...), db: AsyncSession = Depends(get_db),):
    try:
        restricted = defaultdict(set)
        positions = ["QB", "RB", "WR"]
        still_restricting = {pos: True for pos in positions}

        for current_week in range(week - 1, 0, -1):
            if not any(still_restricting.values()):
                break

            pick_stmt = select(WeeklyPick).filter_by(
                user_email=user_email,
                week=current_week,
                league_id=league_id,
                season=season
            )
            pick_result = await db.execute(pick_stmt)
            pick = pick_result.scalars().first()

            score_stmt = select(WeeklyScore).filter_by(
                user_email=user_email,
                week=current_week,
                league_id=league_id,
                season=season
            )
            score_result = await db.execute(score_stmt)
            score = score_result.scalars().first()

            if not pick or not score:
                for pos in positions:
                    still_restricting[pos] = False
                break

            for pos in positions:
                if not still_restricting[pos]:
                    continue

                player_id = getattr(pick, pos.lower(), None)
                pts = getattr(score, f"{pos.lower()}_points", 0)

                if player_id and pts and pts > 0:
                    restricted[pos.lower()].add(player_id)
                else:
                    still_restricting[pos] = False

        return {pos: list(ids) for pos, ids in restricted.items()}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Endpoint 3: Get players with stats ----------
@router.get("/players/{position}/with-stats")
async def get_players_with_stats(position: str, seasons: Optional[List[int]] = Query(None), db: AsyncSession = Depends(get_db)):
    position_upper = position.upper()

    stat_field = {
        "QB": PlayerGameStat.passing_yards,
        "RB": PlayerGameStat.rushing_yards,
        "WR": PlayerGameStat.receiving_yards,
    }.get(position_upper)

    if not stat_field:
        raise HTTPException(status_code=400, detail="Invalid position")

    try:
        stmt = (
                select(
                    Player.id,
                    Player.player_id,
                    Player.player_name,
                    Player.position,
                    Team.id.label("team_id"),
                    Team.name.label("team_name"),
                    func.coalesce(func.sum(stat_field), 0).label("total_yards"),
                )
                .outerjoin(PlayerGameStat, Player.player_id == PlayerGameStat.player_id)
                .outerjoin(NFLGame, PlayerGameStat.game_id == NFLGame.id)
                .outerjoin(Team, Team.id == Player.team_id)
                .where(Player.active.is_(True))
            )

        # Position handling
        if position_upper == "WR":
            stmt = stmt.where(Player.position.in_(["WR", "TE"]))
        else:
            stmt = stmt.where(Player.position == position_upper)

        # Seasonal filter (THIS is the key addition)
        if seasons:
            stmt = stmt.where(NFLGame.season.in_(seasons))

        stmt = stmt.group_by(
            Player.id,
            Player.player_id,
            Player.player_name,
            Player.position,
            Team.id,
            Team.name,
        ).order_by(func.coalesce(func.sum(stat_field), 0).desc())

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "player_id": player_id,
                "player_name": player_name,
                "position": position_upper,
                "team": {
                    "id": team_id,
                    "name": team_name,
                },
                "total_yards": int(total_yards),
            }
            for (
                _,
                player_id,
                player_name,
                _position,
                team_id,
                team_name,
                total_yards,
            ) in rows
        ]

    except Exception as e:
        logger.error(f"Failed to get players with stats for position {position_upper}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving players with stats")
    
# ---------- Endpoint 4: Get player weekly stats ----------
@router.get("/players/{player_id}/stats", response_model=List[schemas.PlayerGameStatOut])
async def get_player_weekly_stats(player_id: int, seasons: Optional[List[int]] = Query(None), db: AsyncSession = Depends(get_db)
):
    try:
        stmt = (
            select(PlayerGameStat)
            .outerjoin(NFLGame, PlayerGameStat.game_id == NFLGame.id)
            .options(
                joinedload(PlayerGameStat.player),
                joinedload(PlayerGameStat.game)
            )
            .filter(PlayerGameStat.player_id == player_id)
        )

        if seasons:
            # keep behaviour: include stats where NFLGame is null (historical / orphan entries)
            stmt = stmt.filter(
                (NFLGame.season.in_(seasons)) | (NFLGame.id.is_(None))
            )

        stmt = stmt.order_by(
            NFLGame.season.asc().nullslast(),
            NFLGame.week.asc().nullslast()
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Failed to get player stats for player_id={player_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving player stats")


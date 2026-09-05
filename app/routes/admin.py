# file: app/routes/admin.py

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from app.database import get_db
from app.models import (League, WeeklyScore, LeagueMember, Season, NFLGame,
                        Player, PositionStreak, AllPositionStreak, LeagueSeasonMember)
from services.scoring import score_week
from services.load_player_game_stats import load_player_stats_for_week
from app.utils.season import get_current_season, get_current_week
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

# --------- Season readiness: what still needs doing before week 1 ---------
@router.get("/season/{year}/readiness")
async def season_readiness(year: int, db: AsyncSession = Depends(get_db)):
    """
    Read-only pre-flight for a season. Answers "what have I forgotten?"
    without having to remember the setup steps. Changes nothing.
    """
    issues = []

    # --- Season row -------------------------------------------------------
    season = (await db.execute(select(Season).filter_by(year=year))).scalars().first()
    current_years = (await db.execute(
        select(Season.year).filter_by(is_current=True).order_by(Season.year)
    )).scalars().all()

    if not season:
        issues.append(f"No seasons row for {year}. Insert one before anything else.")
    elif not season.is_current:
        issues.append(f"Season {year} exists but is_current is false.")
    if len(current_years) > 1:
        issues.append(
            f"{len(current_years)} seasons flagged is_current ({current_years}); "
            "get_current_season() picks arbitrarily. Exactly one should be true."
        )

    # --- NFL games --------------------------------------------------------
    reg_games = (await db.execute(
        select(func.count(NFLGame.id))
        .filter(NFLGame.season == year, NFLGame.stage == "Regular Season")
    )).scalar_one()
    reg_weeks = (await db.execute(
        select(func.count(distinct(NFLGame.week)))
        .filter(NFLGame.season == year, NFLGame.stage == "Regular Season")
    )).scalar_one()
    undated = (await db.execute(
        select(func.count(NFLGame.id))
        .filter(NFLGame.season == year, NFLGame.stage == "Regular Season",
                NFLGame.date.is_(None))
    )).scalar_one()

    if reg_games == 0:
        issues.append(f"No {year} regular-season games. Run scripts/load_games.py with SEASON={year}.")
    elif reg_weeks < 18:
        issues.append(f"Only {reg_weeks} of 18 regular-season weeks present for {year}.")
    if undated:
        issues.append(f"{undated} {year} games have no kickoff date; week detection will be wrong.")

    # --- Players ----------------------------------------------------------
    active_players = (await db.execute(
        select(func.count(Player.id)).filter(Player.active.is_(True))
    )).scalar_one()
    if active_players == 0:
        issues.append("No active players. Run scripts/load_players.py.")

    # --- Per-league -------------------------------------------------------
    leagues = (await db.execute(select(League))).scalars().all()
    league_reports = []
    for lg in leagues:
        members = (await db.execute(
            select(func.count(LeagueMember.id)).filter(LeagueMember.league_id == lg.id)
        )).scalar_one()
        dirty_pos = (await db.execute(
            select(func.count(PositionStreak.id)).filter(
                PositionStreak.league_id == lg.id,
                (PositionStreak.current_streak != 0) | (PositionStreak.last_updated_week.isnot(None)),
            )
        )).scalar_one()
        dirty_all = (await db.execute(
            select(func.count(AllPositionStreak.id)).filter(
                AllPositionStreak.league_id == lg.id,
                (AllPositionStreak.current_streak != 0) | (AllPositionStreak.last_updated_week.isnot(None)),
            )
        )).scalar_one()

        checkin = {"in": 0, "out": 0, "pending": 0}
        rows = (await db.execute(
            select(LeagueSeasonMember.status, func.count(LeagueSeasonMember.id))
            .filter(
                LeagueSeasonMember.league_id == lg.id,
                LeagueSeasonMember.season_year == year,
            )
            .group_by(LeagueSeasonMember.status)
        )).all()
        for st, n in rows:
            checkin[st] = n
        season_opened = sum(checkin.values()) > 0
        if not season_opened:
            issues.append(
                f"League {lg.id} '{lg.name}' has no {year} check-in rows; every member "
                "is scored by default until the season is opened."
            )
        elif checkin["pending"]:
            issues.append(
                f"League {lg.id} '{lg.name}': {checkin['pending']} member(s) have not "
                f"confirmed in/out for {year}."
            )

        rolled_over = lg.season_year == year
        if not rolled_over:
            issues.append(
                f"League {lg.id} '{lg.name}' still season_year={lg.season_year}; "
                f"the {year} scoring job will skip it entirely."
            )
        if dirty_pos or dirty_all:
            issues.append(
                f"League {lg.id} '{lg.name}' has {dirty_pos + dirty_all} streak rows carried "
                f"over from a previous season; they will seed week 1."
            )

        league_reports.append({
            "id": lg.id,
            "name": lg.name,
            "season_year": lg.season_year,
            "rolled_over": rolled_over,
            "members": members,
            "stale_streak_rows": dirty_pos + dirty_all,
            "season_opened": season_opened,
            "checkin": checkin,
        })

    return {
        "season": year,
        "ready": not issues,
        "checks": {
            "season_row": bool(season),
            "is_current": bool(season and season.is_current),
            "seasons_flagged_current": current_years,
            "regular_season_games": reg_games,
            "regular_season_weeks": reg_weeks,
            "games_missing_date": undated,
            "active_players": active_players,
        },
        "leagues": league_reports,
        "issues": issues,
    }


# --------- Generate weekly scoring from business logic and write to DB ---------
@router.post("/run-weekly")
async def run_weekly_tasks(
    week_number: int | None = Query(None, description="Optional week number, e.g. 1-18"),
    season: int | None = Query(None, description="Optional season year, e.g. 2024"),
    session: AsyncSession = Depends(get_db),
):
    # 🧠 Auto-detect season and week if not provided
    if season is None:
        current_season_obj = await get_current_season(session)
        if current_season_obj is None:
            season = datetime.utcnow().year  # fallback to current year
        else:
            season = current_season_obj.year

    if week_number is None:
        detected_week = await get_current_week(session, season)

        # If we're already in the final week window, lock to previous week
        if detected_week >= 18:
            week_number = 17
        else:
            week_number = detected_week - 1
                    #adding minus one since it pulled the week based on Tues..
        if week_number is None:
            week_number = 1

    if week_number < 1 or week_number > 18:
        raise HTTPException(status_code=400, detail="Invalid week number")

    week_str = f"Week {week_number}"

    # ✅ Launch async background tasks properly
    await load_player_stats_for_week(season, week_str)
    await run_scoring_for_all_leagues(week_number, season)

    return {"message": f"✅ Background tasks running for Week {week_number}, Season {season}"}

async def run_scoring_for_all_leagues(week_number: int, season: int):
    async for db in get_db():
        result = await db.execute(select(League).filter_by(season_year=season))
        leagues = result.scalars().all()

        for league in leagues:
            # count users in league (roster, not score history -- a season-scoped
            # WeeklyScore count would be 0 == 0 in week 1 and skip scoring entirely)
            user_result = await db.execute(
                select(func.count(LeagueMember.id))
                .filter(LeagueMember.league_id == league.id)
            )
            total_users = user_result.scalar_one()

            # count scores for this week
            week_result = await db.execute(
                select(func.count(WeeklyScore.id))
                .filter_by(
                    league_id=league.id,
                    week=week_number,
                    season=season
                )
            )
            scored_users = week_result.scalar_one()

            if total_users and scored_users >= total_users:
                print(f"⏭️ Week {week_number} fully scored for League {league.id}, skipping.")
                continue

            print(f"✅ Scoring League {league.name} (Week {week_number})")
            await score_week(week_number, season, league.id)

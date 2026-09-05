# app/routes/picks.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import and_
from pydantic import ValidationError

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app import crud
from app import models as m
from app import schemas as s
from app.database import get_db
from app.utils.season import get_current_week

router = APIRouter()

def orm_to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def normalize_to_utc(dt):
    """Return an aware datetime in UTC. If dt is None -> None.
       If naive, assume UTC (best-effort)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # If DB stored naive datetimes, assume UTC. If yours are stored in a different tz,
        # change this assumption accordingly.
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# GET all picks, optional query params season and league_id
@router.get("/picks/", response_model=List[s.PickOut])
async def read_picks(season: Optional[int] = None, league_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    return await crud.get_all_picks(db, season=season, league_id=league_id)

# POST create or update a pick
@router.post("/picks/", response_model=s.PickOut)
async def create_or_update_user_pick(request: Request, pick: s.PickCreate, db: AsyncSession = Depends(get_db)):
    print("✅ Received pick in route:", pick.model_dump())
    body = await request.json()
    print("📦 Raw request body:", body)
    print("✅ Parsed pick:", pick.model_dump())
    return await crud.create_or_update_pick(db, pick)

# GET picks for a specific user, week, league, and season
@router.get("/picks/email/{user_email}/week/{week}/league/{league_id}/season/{season}", response_model=List[s.PickOut])
async def get_user_picks_for_week_and_league(user_email: str, week: int, league_id: int, season: int, db: AsyncSession = Depends(get_db)):
    print(f"[DEBUG] get_user_picks_for_week_and_league called with user_email={user_email}, week={week}, league_id={league_id}, season={season}")
    
    stmt = select(m.WeeklyPick).filter_by(
        user_email=user_email,
        week=week,
        league_id=league_id,
        season=season
    )
    result = await db.execute(stmt)
    picks = result.scalars().all()
    
    print(f"[DEBUG] Found picks: {picks}")
    return picks

# GET picks with game-time visibility logic (all user picks with weekly scoring)
@router.get("/picks/league/{league_id}/season/{season}/with-weeklyhits", response_model=Dict[str, Any],)
async def get_picks_with_weekly_scores(league_id: int, season: int, db: AsyncSession = Depends(get_db)):
    def L(msg: str):
        print(f"? In with-WeeklyHits: {msg}", flush=True)

    try:
        # -------------------------
        # Step 1: Load all picks & scores
        # -------------------------
        pick_stmt = (
            select(m.WeeklyPick)
            .options(
                selectinload(m.WeeklyPick.user),
                selectinload(m.WeeklyPick.league),
            )
            .where(m.WeeklyPick.league_id == league_id, m.WeeklyPick.season == season)
        )
        picks_result = await db.execute(pick_stmt)
        all_picks = picks_result.unique().scalars().all()

        score_stmt = select(m.WeeklyScore).where(m.WeeklyScore.league_id == league_id, m.WeeklyScore.season == season)
        scores_result = await db.execute(score_stmt)
        all_scores = scores_result.scalars().all()

        L(f"loaded picks count={len(all_picks)}, loaded scores count={len(all_scores)}")

        # -------------------------
        # Step 2: Current week + now
        # -------------------------
        current_week = await get_current_week(db, season)
        now = datetime.now(timezone.utc)
        L(f"current_week={current_week}, now={now}")

        # -------------------------
        # Step 3: Collect all player IDs from picks
        # -------------------------
        player_ids = {int(pid) for pick in all_picks for pos in ["qb", "rb", "wr"] if (pid := getattr(pick, pos))}

        player_team_map = {}
        if player_ids:
            players = (
                await db.execute(
                    select(m.Player.player_id, m.Player.team_id)
                    .where(
                        and_(
                            m.Player.player_id.in_(player_ids),
                            m.Player.active.is_(True)
                        )
                    )
                )
            ).all()
            player_team_map = {pid: tid for pid, tid in players}

        # Step 3 is confirmed working, remove extra debug
        L(f"player_team_map keys count={len(player_team_map)}")

        # -------------------------
        # Step 4: Collect all games for current week
        # -------------------------
        games = (await db.execute(
            select(m.NFLGame)
            .where(
                m.NFLGame.season == season,
                m.NFLGame.week == f"Week {current_week}",
                m.NFLGame.stage == "Regular Season"
            )
        )).scalars().all()

        team_to_date = {}
        for idx, g in enumerate(games):
            gdate = g.date.replace(tzinfo=timezone.utc) if g.date.tzinfo is None else g.date
            if g.home_team_id:
                team_to_date[g.home_team_id] = gdate
            if g.away_team_id:
                team_to_date[g.away_team_id] = gdate

        # Step 4 is confirmed working, remove verbose game debug
        L(f"team_to_date mapping size={len(team_to_date)}")

        # -------------------------
        # Step 5: Process picks per user with detailed validation logging
        # -------------------------
        validated_picks = []

        for pick in all_picks:
            try:
                L(f"\n=== START pick loop user={pick.user_email}, week={pick.week} ===")

                pick_dict = {
                    "id": pick.id,
                    "user_email": pick.user_email,
                    "league_id": pick.league_id,
                    "season": pick.season,
                    "week": pick.week,
                    "timestamp": pick.timestamp,
                }

                # User schema
                if pick.user:
                    user_dict = {
                        "id": pick.user.id,
                        "email": pick.user.email,
                        "name": pick.user.name,
                        "leagues": [
                            {"id": l.id, "name": l.name} for l in getattr(pick.user, "leagues", []) or []
                        ],
                    }
                    pick_dict["user"] = s.UserSummary(**user_dict)
                else:
                    pick_dict["user"] = None

                # QB/RB/WR visibility
                show_flags = {}
                for pos in ["qb", "rb", "wr"]:
                    pid_str = getattr(pick, pos, None)
                    pid = None
                    show = False

                    if pid_str:
                        try:
                            pid = int(pid_str)
                        except Exception:
                            L(f"⚠️ Could not convert {pos.upper()} pid={pid_str} to int")
                            pid = None

                    team_id = player_team_map.get(pid)
                    gdate = team_to_date.get(team_id) if team_id else None

                    if pid:
                        if pick.week < current_week:
                            show = True
                        elif pick.week > current_week:
                            show = False  # 🚫 Never show future week picks
                        elif gdate and now >= gdate:
                            show = True
                        else:
                            show = False


                    pick_dict[pos] = str(pid if show else 0)
                    show_flags[pos] = show

                    # Additional debug: track why a pick is hidden
                    if not show:
                        reason = "week<current_week" if pick.week < current_week else f"game not started or missing gdate ({gdate})"
                        L(f"{pos.upper()} hidden for user={pick.user_email}, reason={reason}")

                pick_dict.update(
                    show_qb=show_flags.get("qb", False),
                    show_rb=show_flags.get("rb", False),
                    show_wr=show_flags.get("wr", False)
                )

                # Construct PickOut
                try:
                    po = s.PickOut(**pick_dict)
                    validated_picks.append(po)
                    L(f"✅ PickOut added for user={pick.user_email}: qb={pick_dict['qb']}, rb={pick_dict['rb']}, wr={pick_dict['wr']}")
                except ValidationError as ve:
                    L(f"❌ PickOut validation failed for user={pick.user_email}, week={pick.week}")
                    L(f"Pick dict: {pick_dict}")
                    L("Field-level validation errors:")
                    for e in ve.errors():
                        L(f" - field: {e['loc']}, type: {e['type']}, msg: {e['msg']}")

                L(f"PickOut keys: {list(pick_dict.keys())}, user type: {type(pick_dict['user'])}")
                L(f"=== END pick loop user={pick.user_email} ===\n")

            except Exception as ex:
                L(f"⚠️ Exception processing pick for user={pick.user_email}, week={pick.week}: {ex}")

        # -------------------------
        # Step 6: Weekly scores
        # -------------------------
        validated_scores = [s.WeeklyScoreRead(**orm_to_dict(score)) for score in all_scores]
        L(f"RETURN picks={len(validated_picks)}, scores={len(validated_scores)}")

        return {"picks": validated_picks, "weekly_hits": validated_scores}

    except Exception as e:
        L(f"UNCAUGHT ERROR: {e}")
        return {"picks": [], "weekly_hits": []}

# GET locked players by user - players that cannot be be picked for the current week based on business logic
@router.get("/locked_players", response_model=dict)
async def get_locked_players(week: int, season: int, league_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns player IDs and names for QB/RB/WR whose game start has passed for the given week and season.
    Only considers players whose position is QB, RB, or WR.
    """
    POSITIONS = ["QB", "RB", "WR"]

    # Step 1: Fetch NFL games for the week and season (Regular Season only)
    games = (await db.execute(
        select(m.NFLGame)
        .where(
            m.NFLGame.season == season,
            m.NFLGame.week == f"Week {week}",
            m.NFLGame.stage == "Regular Season"
        )
    )).scalars().all()

    # Map team_id -> game start datetime
    team_to_date = {}
    for g in games:
        gdate = g.date.replace(tzinfo=timezone.utc) if g.date.tzinfo is None else g.date
        if g.home_team_id:
            team_to_date[g.home_team_id] = gdate
        if g.away_team_id:
            team_to_date[g.away_team_id] = gdate

    # print(f"[LOCKED_PLAYERS] team_to_date mapping size={len(team_to_date)}")

    # Step 2: Fetch all players for QB/RB/WR
    players_stmt = (
        select(m.Player)
        .options(joinedload(m.Player.team))
        .where(m.Player.position.in_(POSITIONS),
         m.Player.active.is_(True) 
         )
    )
    players = (await db.execute(players_stmt)).scalars().all()

    # Step 3: Determine locked players by comparing game start vs now
    now = datetime.now(timezone.utc)
    locked = {pos: [] for pos in POSITIONS}

    for p in players:
        if not p.team or not p.team.id:
            continue  # skip players without a team
        game_date = team_to_date.get(p.team.id)
        if game_date:
            gd = normalize_to_utc(game_date)
            if gd <= now:
                locked[p.position].append({
                    "player_id": p.player_id,
                    "player_name": p.player_name
                })
                # print(f"[LOCKED_PLAYERS] {p.position} locked: {p.player_name} ({p.player_id}) game_time={gd} now={now}")

    # Deduplicate by player_id just in case
    for pos in locked:
        seen = set()
        deduped = []
        for pl in locked[pos]:
            if pl["player_id"] not in seen:
                deduped.append(pl)
                seen.add(pl["player_id"])
        locked[pos] = deduped

    print(f"[LOCKED_PLAYERS] Final locked players by position: {locked}")

    # Step 4: Prepare output for frontend (only IDs)
    locked_ids = {pos: [pl["player_id"] for pl in locked[pos]] for pos in POSITIONS}
    
    return locked_ids

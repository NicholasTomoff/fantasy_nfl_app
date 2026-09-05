from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, WeeklyScore, WeeklyPick, Player, LeagueMember
from sqlalchemy.orm import joinedload

router = APIRouter()

from sqlalchemy.orm import joinedload

async def get_user_picks_for_week(db: AsyncSession, user_email: str, week: int, season: int, league_id: int):
    print("✅ In users loop before fetching their picks:", user_email)

    result = await db.execute(
        select(WeeklyPick)
        .options(
            joinedload(WeeklyPick.user),  # Load related User object
            joinedload(WeeklyPick.league)  # ← if you add this relationship to model
        )
        .filter_by(
            user_email=user_email,
            week=week,
            season=season,
            league_id=league_id,
        )
    )
    pick = result.scalars().unique().one_or_none()  # ✅ fixed order
    if not pick:
        return {"QB": "-", "RB": "-", "WR": "-"}

    return {
        "QB": pick.qb or "-",
        "RB": pick.rb or "-",
        "WR": pick.wr or "-",
        # You can now also access pick.user if needed (e.g., name or ID)
    }

async def get_player_names_by_ids(db: AsyncSession, player_ids):
    if not player_ids:
        print("⚠️ No player_ids passed to get_player_names_by_ids")
        return {}

 #   print(f"✅ In get_player_names_by_ids: {player_ids}")

    result = await db.execute(
        select(Player)
        .options(joinedload(Player.team))
        .where(Player.player_id.in_(player_ids))
    )
    players = result.scalars().unique().all()

 #   print(f"✅ Found {len(players)} players in DB")
    for p in players:
        print(f"🔍 DB Player Match: id={p.player_id}, name={p.player_name}")

    return {player.player_id: player for player in players}

# Get standings; for each user in a league, points, current week picks, current week streaks and bonus, max projected points possible
@router.get("/standings")
async def get_standings(league_id: int, week: int, season: int, db: AsyncSession = Depends(get_db), ):
    print(f"✅ In standings: league_id={league_id}, season={season}, week={week}")

    # Step 1: Get league members with eager loaded memberships
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.memberships).joinedload(LeagueMember.league),
            joinedload(User.hosted_leagues)  # Leagues they host

        )
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .filter(LeagueMember.league_id == league_id)
    )
    users = result.scalars().unique().all()
    print(f"👥 Found {len(users)} users in league {league_id}")
    print(f"👥 Season {season}  Week {week}")

    if not users:
        return []

    emails_in_league = [u.email for u in users]

    # Step 2: Get distinct emails with scores this week
    score_result = await db.execute(
        select(WeeklyScore)
        .filter(
            WeeklyScore.week == week,
            WeeklyScore.season == season,
            WeeklyScore.league_id == league_id,
            WeeklyScore.user_email.in_(emails_in_league),
        )
    )
    all_scores = score_result.scalars().unique().all()
    score_map = {score.user_email: score for score in all_scores}

    standings = []
    all_player_ids = set()
    user_picks_map = {}

    for user in users:
        email = user.email
        name = user.name

        picks = await get_user_picks_for_week(db, email, week, season, league_id)
        user_picks_map[email] = picks
        for pos in ["QB", "RB", "WR"]:
            pid = picks.get(pos)
            if pid and pid != "-":
                try:
                    all_player_ids.add(int(pid))  # Convert string to int for Player table match
                except ValueError:
                    print(f"⚠️ Invalid player ID (not an int): {pid}")


    print(f"🎯 All player_ids collected before name lookup: {all_player_ids}")

    player_map = await get_player_names_by_ids(db, list(all_player_ids))
    print(f"🎯 All player_ids collected AFTER name lookup: {all_player_ids}")

    for user in users:
        email = user.email
        name = user.name

        weekly_score = score_map.get(email)
        picks = user_picks_map.get(email)
        if not picks:
            picks_named = {"QB": "-", "RB": "-", "WR": "-"}
        else:
            picks_named = {}
            for pos in ["QB", "RB", "WR"]:
                pid = picks.get(pos)
                if pid and pid != "-":
                    player = player_map.get(int(pid))  # 🔥 convert to int before lookup
                    picks_named[pos] = player.player_name if player else "-"
                else:
                    picks_named[pos] = "-"

        qb_points = weekly_score.qb_points if weekly_score else 0
        rb_points = weekly_score.rb_points if weekly_score else 0
        wr_points = weekly_score.wr_points if weekly_score else 0
        triple_bonus = weekly_score.all_positions_bonus if weekly_score else 0

        weekly_points = qb_points + rb_points + wr_points + triple_bonus

        standings.append(
            {
                "user_name": name,
                "user_email": email,
                "total_points": weekly_score.total_points if weekly_score else 0,
                "weekly_points": weekly_points,
                "streaks": {
                    "QB": weekly_score.qb_streak if weekly_score else 0,
                    "RB": weekly_score.rb_streak if weekly_score else 0,
                    "WR": weekly_score.wr_streak if weekly_score else 0,
                },
                "triple_streak": triple_bonus,
                "picks": picks_named,
            }
        )

    standings.sort(key=lambda x: x["total_points"], reverse=True)
    return standings

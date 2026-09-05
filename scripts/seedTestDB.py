import os
os.environ["FANTASY_DB"] = "test_fantasy.db"  # ✅ Set before DB import

import sys
import shutil
import random
from datetime import datetime
from faker import Faker
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.database import engine, async_session
from app.models import User, League, LeagueMember, WeeklyPick, NFLGame, Player, PlayerGameStat
from app.auth import get_password_hash

TEST_DB_NAME = "test_fantasy.db"
SOURCE_DB_NAME = "fantasy.db"

# Remove old test DB if exists
if os.path.exists(TEST_DB_NAME):
    os.remove(TEST_DB_NAME)
    print(f"🧹 Removed existing {TEST_DB_NAME}")

# Copy fresh DB
shutil.copyfile(SOURCE_DB_NAME, TEST_DB_NAME)
print(f"📂 Copied {SOURCE_DB_NAME} → {TEST_DB_NAME}")

fake = Faker()
NUM_USERS = 10
NUM_LEAGUES = 3
WEEKS = list(range(1, 19))  # Weeks 1 to 18 inclusive
POSITIONS = ["QB", "RB", "WR"]

async def seed():
    async with async_session() as session:
        print("🛠 Starting seed function...")
        print(f"🛠 Using DB file: {engine.url}")
        print("🚀 Seeding test users...")

        fixed_password = get_password_hash("testpassword123")
        users = []

        # Load NFL games for 2024 season, group by week (lowercase keys)
        result = await session.execute(select(NFLGame).filter(NFLGame.season == 2024))
        games = result.scalars().all()
        week_ids = {}
        for g in games:
            week_ids.setdefault(g.week.lower(), []).append(g.id)

        print("\n=== Count of games per week (lowercase keys) ===")
        for wk, ids in sorted(week_ids.items()):
            print(f"{wk}: {len(ids)} games")

        print("\n=== Sample PlayerGameStat entries ===")
        result = await session.execute(select(PlayerGameStat).limit(10))
        player_stats_sample = result.scalars().all()
        for stat in player_stats_sample:
            print(f"Stat: player_id={stat.player_id}, game_id={stat.game_id}, passing_yards={stat.passing_yards}")

        # Create users
        for _ in range(NUM_USERS):
            user = User(
                name=fake.name(),
                email=fake.email(),
                hashed_password=fixed_password
            )
            session.add(user)
            users.append(user)
        await session.commit()

        print("🏈 Creating leagues and adding users...")
        leagues = []
        for _ in range(NUM_LEAGUES):
            league = League(
                name=f"{fake.word().capitalize()} League",
                created_by_user_id=random.choice(users).id,
                season_year=2024
            )
            session.add(league)
            leagues.append(league)
        await session.commit()

        print("➕ Adding users to leagues...")
        for league in leagues:
            member_sample = random.sample(users, k=random.randint(5, NUM_USERS))
            for user in member_sample:
                session.add(LeagueMember(user_id=user.id, league_id=league.id))
        await session.commit()

        print("🎯 Seeding weekly picks with simulated hits and misses...")

        result = await session.execute(select(Player))
        players = result.scalars().all()
        result = await session.execute(select(PlayerGameStat))
        stats = result.scalars().all()

        print(f"📊 Total players loaded: {len(players)}")
        print(f"📊 Total player stats loaded: {len(stats)}")

        # Index stats by (player_id, game_id)
        stats_by_player_game = {}
        for stat in stats:
            key = (int(stat.player_id), stat.game_id)
            stats_by_player_game.setdefault(key, []).append(stat)

        total_picks = 0

        for user in users:
            print(f"👤 Processing picks for user: {user.email}")

            # Get all leagues this user belongs to
            result = await session.execute(select(LeagueMember).filter_by(user_id=user.id))
            member_leagues = result.scalars().all()
            league_ids = [lm.league_id for lm in member_leagues]

            for league_id in league_ids:
                for week in WEEKS:
                    week_str = f"week {week}".lower()
                    result = await session.execute(
                        select(NFLGame).filter(
                            NFLGame.season == 2024,
                            NFLGame.week.ilike(week_str)
                        )
                    )
                    game_ids_for_week = [g.id for g in result.scalars().all()]

                    picks_for_week = {"QB": None, "RB": None, "WR": None}

                    for pos in POSITIONS:
                        eligible_players = [p for p in players if p.position == pos]

                        candidates = []
                        for p in eligible_players:
                            for game_id in game_ids_for_week:
                                key = (int(p.player_id), game_id)
                                player_stats_list = stats_by_player_game.get(key, [])

                                for stat in player_stats_list:
                                    is_hit = False
                                    if pos == "QB" and stat.passing_yards and stat.passing_yards >= 300:
                                        is_hit = True
                                    elif pos in ("RB", "WR"):
                                        rushing = stat.rushing_yards or 0
                                        receiving = stat.receiving_yards or 0
                                        tds = (stat.rushing_tds or 0) + (stat.receiving_tds or 0)
                                        if (rushing + receiving >= 125) or tds > 0:
                                            is_hit = True

                                    candidates.append({
                                        "player": p,
                                        "stat": stat,
                                        "game_id": game_id,
                                        "is_hit": is_hit
                                    })

                        if not candidates:
                            continue

                        hit_candidates = [c for c in candidates if c["is_hit"]]
                        miss_candidates = [c for c in candidates if not c["is_hit"]]

                        if random.random() > 0.5 and hit_candidates:
                            chosen = random.choice(hit_candidates)
                        elif miss_candidates:
                            chosen = random.choice(miss_candidates)
                        else:
                            chosen = random.choice(candidates)

                        picks_for_week[pos] = str(chosen["player"].player_id)

                    pick = WeeklyPick(
                        user_email=user.email,
                        week=week,
                        season=2024,
                        league_id=league_id,
                        qb=picks_for_week["QB"],
                        rb=picks_for_week["RB"],
                        wr=picks_for_week["WR"],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    session.add(pick)
                    total_picks += 1

        await session.commit()
        print(f"✅ Seeding complete. Total picks added: {total_picks}")

if __name__ == "__main__":
    asyncio.run(seed())

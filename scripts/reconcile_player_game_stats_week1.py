# file: scripts/reconcile_player_game_stats_week1.py
import asyncio
import json
import pathlib
import os
import sys
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import PlayerGameStat, Player
from app.database import async_engine

JSON_FILE = pathlib.Path(__file__).parent.parent / "player_game_stats_week1_2025.json"

async def reconcile_player_game_stats():
    async with AsyncSession(async_engine) as session:
        if not JSON_FILE.exists():
            print(f"❌ Cannot find JSON file at {JSON_FILE}")
            return

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            stats_data = json.load(f)

        print(f"📥 Loaded {len(stats_data)} entries from {JSON_FILE}")

        inserted_count = 0
        skipped_count = 0
        skipped_missing_players = 0

        for entry in stats_data:
            player_id = entry.get("player_id")
            team_id = entry.get("team_id")
            game_id = entry.get("game_id")

            # Check if already exists
            existing = await session.execute(
                select(PlayerGameStat)
                .filter_by(player_id=player_id, game_id=game_id)
            )
            if existing.scalars().first():
                skipped_count += 1
                continue

            # ⚠️ IMPORTANT: Only check player_id, ignore team_id (reconcile later)
            player_result = await session.execute(
                select(Player).filter_by(player_id=player_id)
            )
            if not player_result.scalars().first():
                skipped_missing_players += 1
                continue

            # Insert PlayerGameStat safely using .get() with defaults
            new_stat = PlayerGameStat(
                player_id=player_id,
                team_id=team_id,  # we still store what JSON provides (can reconcile later)
                game_id=game_id,
                position=entry.get("position"),
                passing_yards=entry.get("passing_yards", 0),
                passing_tds=entry.get("passing_tds", 0),
                rushing_yards=entry.get("rushing_yards", 0),
                rushing_tds=entry.get("rushing_tds", 0),
                receiving_yards=entry.get("receiving_yards", 0),
                receiving_tds=entry.get("receiving_tds", 0),
                receptions=entry.get("receptions", 0)
            )
            session.add(new_stat)
            inserted_count += 1

        await session.commit()

        print(f"✅ Reconciliation complete.")
        print(f"🆕 Inserted new stats: {inserted_count}")
        print(f"⏭️ Skipped (already existed): {skipped_count}")
        print(f"🚫 Skipped (missing player records): {skipped_missing_players}")

if __name__ == "__main__":
    asyncio.run(reconcile_player_game_stats())

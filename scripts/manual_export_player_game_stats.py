import sys
import os
import asyncio
import json
import pathlib
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import NFLGame, Player
from app.database import async_engine

# Load env
from dotenv import load_dotenv
project_root = pathlib.Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / ".env")

API_KEY = os.environ.get("RAPIDAPI_KEY")
BASE_URL = "https://api-american-football.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-host": "api-american-football.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

STAGE = "Regular Season"

# ---------------- Parse Helper ----------------
def parse_individual_player_stats(group):
    """Collects passing/rushing/receiving stats for each player."""
    player_stats_map = {}

    for entry in group.get("players", []):
        player = entry["player"]
        stats = player_stats_map.setdefault(player["id"], {
            "player_name": player.get("name"),
            "passing_yards": 0,
            "passing_tds": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "receiving_yards": 0,
            "receiving_tds": 0,
            "receptions": 0,
            "position": player.get("position", "N/A")
        })

        for s in entry.get("statistics", []):
            name = s.get("name", "").lower()
            value = s.get("value", "0")
            try:
                value = int(value)
            except:
                continue

            if name == "passing touch downs":
                stats["passing_tds"] += value
            elif name == "rushing touch downs":
                stats["rushing_tds"] += value
            elif name == "receiving touch downs":
                stats["receiving_tds"] += value
            elif name == "total receptions":
                stats["receptions"] += value
            elif name == "yards":
                gname = group.get("name", "").lower()
                if gname == "passing":
                    stats["passing_yards"] += value
                elif gname == "rushing":
                    stats["rushing_yards"] += value
                elif gname == "receiving":
                    stats["receiving_yards"] += value

    return player_stats_map


# ---------------- Fetch Helper ----------------
async def fetch_game_stats(client: httpx.AsyncClient, game_id: int):
    url = f"{BASE_URL}/games/statistics/players"
    params = {"id": game_id}
    response = await client.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("response", [])


# ---------------- Position Lookup ----------------
async def get_positions_for_players(session: AsyncSession, player_ids: list[int]):
    if not player_ids:
        return {}
    result = await session.execute(select(Player.player_id, Player.position).where(Player.player_id.in_(player_ids)))
    return {pid: pos for pid, pos in result.all()}


# ---------------- Main Export ----------------
async def manual_export(season: int, target_week: str, export_file: str):
    async with AsyncSession(async_engine) as session:
        result = await session.execute(
            select(NFLGame).filter_by(stage=STAGE, week=target_week, season=season)
        )
        games = result.scalars().all()

        if not games:
            print("⚠️ No games found for given week and season.")
            return

        all_stat_rows = []
        all_player_ids = set()

        async with httpx.AsyncClient() as client:
            for game in games:
                try:
                    response = await fetch_game_stats(client, game.id)
                    if not response:
                        print(f"⚠️ Empty response for game {game.id}")
                        continue

                    for team_block in response:
                        team_id = team_block["team"]["id"]
                        player_stats_agg = {}

                        for group in team_block.get("groups", []):
                            group_stats = parse_individual_player_stats(group)
                            for player_id, stats in group_stats.items():
                                if player_id not in player_stats_agg:
                                    player_stats_agg[player_id] = stats
                                else:
                                    for k, v in stats.items():
                                        if isinstance(v, int):
                                            player_stats_agg[player_id][k] += v
                                        elif k == "position" and player_stats_agg[player_id][k] == "N/A":
                                            player_stats_agg[player_id][k] = v

                        for player_id, stats in player_stats_agg.items():
                            all_player_ids.add(player_id)
                            all_stat_rows.append({
                                "player_id": player_id,
                                "player_name": stats["player_name"],
                                "team_id": team_id,
                                "game_id": game.id,
                                "season": game.season,
                                "week": game.week,
                                "position": stats["position"],  # will patch below if "N/A"
                                "passing_yards": stats["passing_yards"],
                                "passing_tds": stats["passing_tds"],
                                "rushing_yards": stats["rushing_yards"],
                                "rushing_tds": stats["rushing_tds"],
                                "receiving_yards": stats["receiving_yards"],
                                "receiving_tds": stats["receiving_tds"],
                                "receptions": stats["receptions"],
                            })

                    print(f"✅ Processed game {game.id}, players: {len(player_stats_agg)}")

                finally:
                    await asyncio.sleep(7)

        # 🔧 Fix missing positions using Player table
        positions_map = await get_positions_for_players(session, list(all_player_ids))
        missing_positions = 0
        for row in all_stat_rows:
            if row["position"] == "N/A":
                db_position = positions_map.get(row["player_id"])
                if db_position:
                    row["position"] = db_position
                else:
                    missing_positions += 1

        if missing_positions:
            print(f"⚠️ {missing_positions} players still have no position after DB lookup.")

        # Write JSON
        export_path = pathlib.Path(export_file)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(all_stat_rows, f, indent=2)
        print(f"💾 Exported {len(all_stat_rows)} player-game stats to {export_path}")


if __name__ == "__main__":
    season = int(sys.argv[1])
    week = sys.argv[2]
    export_file = sys.argv[3]
    asyncio.run(manual_export(season, week, export_file))

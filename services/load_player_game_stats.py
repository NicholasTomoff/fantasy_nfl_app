# file: root/services/load_player_game_stats.py
import sys
import os
import asyncio
import time
from datetime import datetime
import pathlib
import json
import httpx
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import NFLGame, PlayerGameStat, Player
from app.database import async_engine

# ---------- Environment / API KEY ----------
IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"

if not IS_CI:
    from dotenv import load_dotenv
    project_root = pathlib.Path(__file__).parent.parent
    load_dotenv(dotenv_path=project_root / ".env")

API_KEY = os.environ.get("RAPIDAPI_KEY")
if not API_KEY:
    raise RuntimeError(
        "RAPIDAPI_KEY not found. Make sure your .env is loaded locally "
        "or GitHub Actions env is set."
    )

BASE_URL = "https://api-american-football.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-host": "api-american-football.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

STAGE = "Regular Season"  # target stage


# ---------- Helper: Fetch stats ----------
async def fetch_game_stats(client: httpx.AsyncClient, game_id: int):
    url = f"{BASE_URL}/games/statistics/players"
    params = {"id": game_id}

    print(f"🌐 Calling API: {url} with params={params}")
    response = await client.get(url, headers=HEADERS, params=params)
    print(f"🔎 Response status={response.status_code}")
    try:
        print(f"🔎 Preview: {response.text[:200]}...")
    except Exception:
        pass

    response.raise_for_status()
    return response.json().get("response", [])


# ---------- Helper: Parse player stats ----------
def parse_individual_player_stats(group):
    player_stats_map = {}

    for entry in group.get("players", []):
        player = entry["player"]
        stats = player_stats_map.setdefault(player["id"], {
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


# ---------- Main loader ----------
async def load_player_stats_for_week(season: int, target_week: str):
    async with AsyncSession(async_engine) as session:
        result = await session.execute(
            select(NFLGame).filter_by(stage=STAGE, week=target_week, season=season)
        )
        games = result.scalars().all()
        print(f"\n📥 Fetching stats for {len(games)} games in {target_week} {season}...")

        if not games:
            print("⚠️ No games found for given week and season.")
            return

        api_call_count = 0
        stats_saved_count = 0
        errors = []
        all_stat_entries = []
        missing_players = []  # collect missing players for reconciliation

        async with httpx.AsyncClient() as client:
            for game in games:
                existing = await session.execute(
                    select(PlayerGameStat)
                    .join(Player, PlayerGameStat.player_id == Player.player_id)
                    .filter(PlayerGameStat.game_id == game.id)
                    .filter(Player.team_id == PlayerGameStat.team_id)
                )
                if existing.scalars().first():
                    print(f"⏭️ Skipping game {game.id} — stats already loaded.")
                    continue

                try:
                    print(f"📞 Fetching stats for game ID: {game.id}")
                    response = await fetch_game_stats(client, game.id)
                    api_call_count += 1

                    if not response:
                        raise ValueError("Empty API response")

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
                            player_exists = await session.execute(
                                select(Player).filter_by(player_id=player_id)
                            )

                            if not player_exists.scalars().first():
                                print(f"⚠️ Missing player_id={player_id}, team_id={team_id} — inserting stats anyway.")
                                missing_players.append({
                                    "player_id": player_id,
                                    "team_id": team_id,
                                    "game_id": game.id,
                                    "season": season,
                                    "week": target_week,
                                    "position": stats["position"]
                                })

                            stat_entry = PlayerGameStat(
                                player_id=player_id,
                                team_id=team_id,
                                game_id=game.id,
                                position=stats["position"],
                                passing_yards=stats["passing_yards"],
                                passing_tds=stats["passing_tds"],
                                rushing_yards=stats["rushing_yards"],
                                rushing_tds=stats["rushing_tds"],
                                receiving_yards=stats["receiving_yards"],
                                receiving_tds=stats["receiving_tds"],
                                receptions=stats["receptions"]
                            )
                            all_stat_entries.append(stat_entry)
                            stats_saved_count += 1

                    print(f"✅ Processed game {game.id}")

                except Exception as e:
                    error_msg = f"⚠️ Error for game {game.id}: {e}"
                    print(error_msg)
                    errors.append(error_msg)

                finally:
                    await asyncio.sleep(7)  # keep rate limiting delay

        try:
            session.add_all(all_stat_entries)
            await session.commit()
            print(f"✅ Committed {len(all_stat_entries)} player stats to the DB.")
        except Exception as e:
            await session.rollback()
            print(f"❌ Rollback occurred during final commit: {e}")
            errors.append(str(e))

        # Write missing players log
        data_dir = pathlib.Path(__file__).parent.parent / "app" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        missing_file = data_dir / f"missing_players_{season}_{target_week}.json"
        with open(missing_file, "w", encoding="utf-8") as f:
            json.dump(missing_players, f, indent=2)
        print(f"📝 Logged {len(missing_players)} missing players to {missing_file}")

        print(f"\n📊 Weekly Load Summary — Season {season}, {target_week}")
        print(f"📦 Games processed: {len(games)}")
        print(f"📞 API calls made: {api_call_count}")
        print(f"🧮 Stats saved: {stats_saved_count}")
        if errors:
            print(f"❌ Errors encountered for {len(errors)} games or during commit:")
            for e in errors:
                print(f"   - {e}")
                
        if missing_players:
            print(f"⚠️ {len(missing_players)} missing players detected — stats saved anyway.")
            print("Example missing player entries:", missing_players[:5])


        # Export to JSON for inspection
    #    export_path = pathlib.Path(f"/tmp/player_game_stats_export_{season}_{target_week}.json")
    #    print(f"📂 Attempting export to: {export_path.resolve()}")

    #    export_data = [
    #        {
    #            "player_id": stat.player_id,
    #            "team_id": stat.team_id,
    #            "game_id": stat.game_id,
    #            "position": stat.position,
    #            "passing_yards": stat.passing_yards,
    #            "passing_tds": stat.passing_tds,
    #            "rushing_yards": stat.rushing_yards,
    #            "rushing_tds": stat.rushing_tds,
    #            "receiving_yards": stat.receiving_yards,
    #            "receiving_tds": stat.receiving_tds,
    #            "receptions": stat.receptions
    #        }
    #        for stat in all_stat_entries
    #    ]
    #    try:
    #        with open(export_path, "w", encoding="utf-8") as f:
    #            json.dump(export_data, f, indent=2)
    #        print(f"💾 Exported {len(export_data)} stats to {export_path}")
    #    except Exception as e:
    #        import traceback
    #        print(f"❌ Failed to export JSON: {e}")
    #        traceback.print_exc()
    #        raise

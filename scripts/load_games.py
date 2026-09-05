import sys
import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
from app.database import AsyncSession, async_engine
from app.models import NFLGame
from sqlalchemy.future import select

load_dotenv()

API_KEY = os.getenv("RAPIDAPI_KEY")
if not API_KEY:
    raise ValueError("Missing RAPIDAPI_KEY environment variable")

BASE_URL = "https://api-american-football.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-host": "api-american-football.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

SEASON = 2026  # Change per season
LEAGUE_ID = 1  # NFL per API docs
LEAGUE = "NFL"

async def fetch_games_for_season(season: int):
    url = f"{BASE_URL}/games"
    params = {"season": str(season), "league": LEAGUE_ID}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params)
        response.raise_for_status()

        json_data = response.json()
        if "response" not in json_data:
            raise ValueError("❌ 'response' key not found in API result")

        return json_data["response"]

async def load_games_into_db(games, session: AsyncSession):
    new_count = 0
    for item in games:
        game_data = item.get("game", {})
        teams = item.get("teams", {})
        scores = item.get("scores", {})

        game_id = game_data.get("id")
        if not game_id:
            print("⚠️ Skipping game with missing ID")
            continue

        # Check existing asynchronously
        existing_res = await session.execute(select(NFLGame).filter_by(id=game_id))
        existing = existing_res.scalars().first()
        if existing:
                # UPDATE mutable fields (kickoff time, status, scores)
            existing.week = game_data.get("week", existing.week)
            existing.stage = game_data.get("stage", existing.stage)
            existing.datetime = (
                datetime
                .fromtimestamp(game_data["date"]["timestamp"], tz=timezone.utc)
                .replace(tzinfo=None)
            )
            existing.status = game_data.get("status", {}).get("short")

            existing.home_score = scores.get("home", {}).get("total")
            existing.away_score = scores.get("away", {}).get("total")
            
            continue  # Skip if already in DB

        try:
            game_obj = NFLGame(
                id=game_id,
                season=SEASON,
                week=game_data.get("week", "Unknown"),
                stage=game_data.get("stage", "Unknown"),

                date=(
                        datetime
                        .fromtimestamp(game_data["date"]["timestamp"], tz=timezone.utc)
                        .replace(tzinfo=None)
                ),
                status=game_data.get("status", {}).get("short"),

                home_team=teams.get("home", {}).get("name"),
                home_team_id=teams.get("home", {}).get("id"),

                away_team=teams.get("away", {}).get("name"),
                away_team_id=teams.get("away", {}).get("id"),

                home_score=scores.get("home", {}).get("total"),
                away_score=scores.get("away", {}).get("total"),
            )
            session.add(game_obj)
            new_count += 1
        except Exception as e:
            print(f"⚠️ Skipping game {game_id} due to error: {e}")

    await session.commit()
    print(f"✅ Inserted {new_count} new games into the database.")

async def main():
    print(f"📥 Fetching {SEASON} {LEAGUE} games...")
    games = await fetch_games_for_season(SEASON)
    print(f"📦 Fetched {len(games)} games.")

    async with AsyncSession(async_engine) as session:
        await load_games_into_db(games, session)

if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json

from app.models import Player, Team
from app.database import get_db
from sqlalchemy import select

SEASON = 2025
PLAYER_FILENAME = f"app/data/players_{SEASON}.json"
TEAM_FILENAME = f"app/data/teams_{SEASON}.json"


async def load_teams_from_json(db):
    if not os.path.exists(TEAM_FILENAME):
        print(f"Missing file: {TEAM_FILENAME}")
        return

    with open(TEAM_FILENAME, "r") as f:
        teams = json.load(f)

    for entry in teams:
        result = await db.execute(select(Team).where(Team.id == entry["id"]))
        existing_team = result.scalars().first()
        if not existing_team:
            db.add(Team(id=entry["id"], name=entry["name"]))

    await db.commit()
    print(f"Loaded {len(teams)} teams from {TEAM_FILENAME}")


async def load_players_from_json(db):
    if not os.path.exists(PLAYER_FILENAME):
        print(f"Missing file: {PLAYER_FILENAME}")
        return

    with open(PLAYER_FILENAME, "r") as f:
        players = json.load(f)

    # Step 1: mark all existing players inactive for this season load
    await db.execute(
        Player.__table__.update().values(active=False)
    )
    await db.commit()

    for entry in players:
        # lookup team name from teams table
        result = await db.execute(select(Team).where(Team.id == entry["team_id"]))
        team = result.scalars().first()
        team_name = team.name if team else None

        # Check for existing player with same player_id AND team_id
        result = await db.execute(
            select(Player).where(
                Player.player_id == entry["player_id"],
                Player.team_id == entry["team_id"]
            )
        )
        existing = result.scalars().first()

        if existing:
            # Reactivate existing record
            existing.active = True
        else:
            # Insert new player record for this team
            player = Player(
                player_id=entry["player_id"],
                player_name=entry["player_name"],
                position=entry["position"],
                team_id=entry["team_id"],
                team_name=team_name,
                active=True
            )
            db.add(player)

    await db.commit()
    print(f"Loaded {len(players)} players from {PLAYER_FILENAME}")


async def main():
    async for db in get_db():
        await load_teams_from_json(db)
        await load_players_from_json(db)


if __name__ == "__main__":
    asyncio.run(main())

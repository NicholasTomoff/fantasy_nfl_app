import os
import sys
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json

from app.models import Player, Team, PlayerGameStat, NFLGame
from app.database import get_db
from sqlalchemy import select, func

SEASON = 2026

# --- Guards against an incomplete provider response -------------------------
# The RapidAPI team-roster endpoint has returned partial rosters (62 players for
# Detroit in 2026, with Jahmyr Gibbs missing and no paging to follow). The old
# behaviour -- deactivate everyone, then reactivate whoever came back -- turned
# that into real players silently vanishing from the pick lists.
MIN_PLAYERS_PER_TEAM = 40      # below this, a roster is not believable
MIN_TEAMS_EXPECTED = 32
# Players with game stats in this season are kept active even if the fetch omits
# them: they demonstrably played, so the provider is wrong, not the database.
PROTECT_IF_PLAYED_IN = SEASON - 1
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

    # ---- Sanity-check the fetch before trusting it ------------------------
    per_team = {}
    for entry in players:
        per_team[entry["team_id"]] = per_team.get(entry["team_id"], 0) + 1

    thin = {t: n for t, n in per_team.items() if n < MIN_PLAYERS_PER_TEAM}
    problems = []
    if len(per_team) < MIN_TEAMS_EXPECTED:
        problems.append(f"only {len(per_team)} teams in the file (expected {MIN_TEAMS_EXPECTED})")
    if thin:
        problems.append(f"{len(thin)} team(s) under {MIN_PLAYERS_PER_TEAM} players: {thin}")

    if problems:
        for problem in problems:
            print("WARNING: " + problem)
        print("WARNING: the roster fetch looks incomplete -- no one will be deactivated.")

    # ---- Who has earned protection from deactivation ----------------------
    fetched = {(p["player_id"], p["team_id"]) for p in players}

    played = await db.execute(
        select(PlayerGameStat.player_id, PlayerGameStat.team_id)
        .join(NFLGame, NFLGame.id == PlayerGameStat.game_id)
        .where(NFLGame.season == PROTECT_IF_PLAYED_IN)
        .distinct()
    )
    protected = {(pid, tid) for pid, tid in played.all()}
    print(f"{len(protected)} player/team pairs protected by {PROTECT_IF_PLAYED_IN} game stats")

    # ---- Deactivate only what is genuinely gone ---------------------------
    if problems:
        deactivated = 0
    else:
        existing = (await db.execute(select(Player))).scalars().all()
        deactivated = 0
        for p in existing:
            key = (p.player_id, p.team_id)
            if key in fetched or key in protected:
                continue
            if p.active:
                p.active = False
                deactivated += 1
        await db.commit()
    print(f"Deactivated {deactivated} players no longer on any roster")

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

import os
import sys
import json
import time
import argparse
import requests
from dotenv import load_dotenv

# Setup path and env
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

# === Config ===
BASE_URL = "https://api-american-football.p.rapidapi.com"
DEFAULT_API_KEY = "bb818edc98msh0ddc701fde89757p1384c3jsn10b83f27cf2b"
API_KEY = os.getenv("RAPIDAPI_KEY", DEFAULT_API_KEY)

HEADERS = {
    "x-rapidapi-host": "api-american-football.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

LEAGUE_ID = 1  # NFL
DATA_DIR = "app/data"
os.makedirs(DATA_DIR, exist_ok=True)


# === Fetch functions ===
def fetch_teams(season: int):
    print(f"📥 Fetching teams for {season}")
    url = f"{BASE_URL}/teams"
    query = {"league": str(LEAGUE_ID), "season": str(season)}

    response = requests.get(url, headers=HEADERS, params=query)
    response.raise_for_status()
    data = response.json()

    teams = []
    for entry in data.get("response", []):
        team_info = entry.get("team", entry)  # Some responses nest under 'team'
        teams.append({
            "id": team_info["id"],
            "name": team_info["name"]
        })

    return teams


def fetch_players_for_team(team_id, team_name, season):
    print(f"🔍 Fetching players for {team_name} (ID: {team_id})")
    url = f"{BASE_URL}/players"
    query = {"season": str(season), "team": str(team_id)}

    response = requests.get(url, headers=HEADERS, params=query)
    response.raise_for_status()
    data = response.json()

    if not data.get("response"):
        print(f"⚠️ No players found for {team_name}")
        return []

    players = []
    for item in data["response"]:
        player = item.get("player", item)
        players.append({
            "team_id": team_id,
            "team_name": team_name,
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "position": player.get("position")
        })

    return players


# === Main run logic ===
def run(season: int):
    teams_file = os.path.join(DATA_DIR, f"teams_{season}.json")
    players_file = os.path.join(DATA_DIR, f"players_{season}.json")

    # Load or fetch teams
    if os.path.exists(teams_file):
        with open(teams_file, "r") as f:
            nfl_teams = json.load(f)
        print(f"✅ Loaded {len(nfl_teams)} teams from cache.")
    else:
        nfl_teams = fetch_teams(season)
        with open(teams_file, "w") as f:
            json.dump(nfl_teams, f, indent=2)
        print(f"💾 Saved {len(nfl_teams)} teams to {teams_file}")

    # Load previously fetched players (if any)
    all_players = []
    fetched_team_ids = set()
    if os.path.exists(players_file):
        with open(players_file, "r") as f:
            all_players = json.load(f)
        fetched_team_ids = set(p["team_id"] for p in all_players)
        print(f"📂 Loaded {len(all_players)} players from cache.")

    # Fetch remaining teams
    for team in nfl_teams:
        if team["id"] in fetched_team_ids:
            print(f"⏩ Skipping {team['name']} (already fetched)")
            continue

        try:
            players = fetch_players_for_team(team["id"], team["name"], season)
            all_players.extend(players)
        except Exception as e:
            print(f"❌ Error fetching {team['name']}: {e}")
        finally:
            time.sleep(10)  # RapidAPI rate limit buffer

    # Save updated players list
    with open(players_file, "w") as f:
        json.dump(all_players, f, indent=2)

    print(f"🏈 Done: {len(all_players)} total players saved to {players_file}")
    print("🧪 Sample players:", all_players[:3])


# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch NFL teams and players from RapidAPI")
    parser.add_argument("--season", type=int, required=True, help="Season year to fetch (e.g. 2024)")
    args = parser.parse_args()

    run(args.season)

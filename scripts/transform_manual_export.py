import json
import pathlib
from collections import defaultdict

INPUT_FILE = pathlib.Path(__file__).parent.parent / "player_game_stats_week1_2025.json"
OUTPUT_FILE = pathlib.Path(__file__).parent.parent / "player_game_stats_week1_2025_transformed.json"

def transform_manual_export():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    aggregated = defaultdict(lambda: {
        "passing_yards": 0,
        "passing_tds": 0,
        "rushing_yards": 0,
        "rushing_tds": 0,
        "receiving_yards": 0,
        "receiving_tds": 0,
        "receptions": 0,
        "position": "N/A",
        "game_id": None,
        "player_id": None,
        "team_id": None
    })

    for entry in raw_data:
        key = (entry["game_id"], entry["player_id"], entry["team_id"])
        stats = aggregated[key]
        stats["game_id"] = entry["game_id"]
        stats["player_id"] = entry["player_id"]
        stats["team_id"] = entry["team_id"]
        stats["position"] = entry.get("position") or stats["position"]

        group_name = entry.get("statistics")  # actually we check entry's statistics list
        for stat in entry["statistics"]:
            name = stat["name"].lower()
            try:
                value = int(stat["value"])
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
                group = entry.get("group", "").lower() if "group" in entry else ""
                if "passing" in group:
                    stats["passing_yards"] += value
                elif "rushing" in group:
                    stats["rushing_yards"] += value
                elif "receiving" in group:
                    stats["receiving_yards"] += value

    transformed = list(aggregated.values())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(transformed, f, indent=2)

    print(f"✅ Transformed {len(raw_data)} raw entries into {len(transformed)} aggregated player stats.")
    print(f"💾 Saved transformed file to {OUTPUT_FILE}")

if __name__ == "__main__":
    transform_manual_export()

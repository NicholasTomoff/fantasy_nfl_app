import json
import csv

# Load JSON
with open("players_2024.json", "r") as f:
    players = json.load(f)

# Write to CSV
with open("players_2024.csv", "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = players[0].keys()
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(players)

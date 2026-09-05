import requests

BASE_URL = "https://api-american-football.p.rapidapi.com"
API_KEY = "bb818edc98msh0ddc701fde89757p1384c3jsn10b83f27cf2b"

headers = {
    "x-rapidapi-host": "api-american-football.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

params = {
    "team": "31",               # ✅ Rams
    "season": "2025",           # change to 2024 if 2025 not available yet
  #  "league": "1",              # NFL
    "name": "Davante Adams"   # 🔍 filter to specific player
}

url = f"{BASE_URL}/players"
r = requests.get(url, headers=headers, params=params)

print("Status Code:", r.status_code)
print("Response JSON:", r.json())

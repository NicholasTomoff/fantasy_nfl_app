import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()  # This loads .env variables into os.environ

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("VITE_SUPABASE_SERVICE_KEY")

print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_SERVICE_ROLE_KEY:", SUPABASE_SERVICE_ROLE_KEY)

async def fetch_players():
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SUPABASE_URL}/rest/v1/players", headers=headers)
        response.raise_for_status()
        data = response.json()
        print("Data fetched:", data)   # <-- This prints the data
        return data

async def main():
    players = await fetch_players()
    # You can add extra checks here, e.g.:
    print(f"Total players fetched: {len(players)}")

if __name__ == "__main__":
    asyncio.run(main())
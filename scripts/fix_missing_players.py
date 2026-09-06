"""
Restore skill players that an incomplete roster fetch marked inactive.

Talks to the deployed API over HTTPS -- no database tunnel and no browser
console needed. Run it from a normal terminal:

    python scripts/fix_missing_players.py

It previews first and asks before writing anything.

Why this is needed: RapidAPI's team-roster endpoint returns partial rosters
(62 players for Detroit in 2026, with Jahmyr Gibbs missing). load_players.py
used to mark every player inactive and reactivate only whoever came back, so
real players silently disappeared from the pick lists. They were never deleted.

This reactivates players who demonstrably played in the evidence season: they
have player_game_stats rows for a game in that season, on the same team.
"""

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BACKEND = "https://fantasy-nfl-app.fly.dev"


def _post(url: str, token: str | None = None, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"\n{url}\n  HTTP {e.code}: {body[:400]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"\nCould not reach {url}\n  {e.reason}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", default=DEFAULT_BACKEND)
    ap.add_argument("--season", type=int, default=2025,
                    help="Season whose game stats prove a player is real (default: 2025)")
    ap.add_argument("--email", help="Your login email (prompted if omitted)")
    ap.add_argument("--yes", action="store_true",
                    help="Apply without asking. Previews and asks by default.")
    args = ap.parse_args()

    email = args.email or input("Email: ").strip()
    # Typed into your terminal, never echoed and never stored.
    password = getpass.getpass("Password: ")

    print("\nSigning in...")
    login = _post(f"{args.backend}/api/users/login",
                  payload={"email": email, "password": password})
    token = login.get("token")
    if not token:
        raise SystemExit("Login succeeded but returned no token.")
    print(f"  signed in as {login.get('user', {}).get('name') or email}")

    endpoint = f"{args.backend}/admin/players/reactivate-from-stats?season={args.season}"

    print(f"\nPreviewing (evidence season {args.season})...")
    preview = _post(endpoint, token)
    print(f"  players that would be reactivated: {preview['matched']}")
    print(f"  by position: {preview.get('by_position') or '{}'}")
    print(f"  currently active in total: {preview.get('active_players_now')}")
    for p in preview.get("sample", [])[:10]:
        print(f"     {p['position']:<3} {p['name']} ({p['team']})")

    if not preview["matched"]:
        print("\nNothing to do.")
        return

    if not args.yes:
        answer = input(f"\nReactivate these {preview['matched']} players? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled. Nothing was changed.")
            return

    print("\nApplying...")
    result = _post(f"{endpoint}&apply=true", token)
    print(f"  reactivated: {result['matched']}")
    print(f"  active players now: {result['active_players_now']}")
    print("\nDone. Reload the pick page to see them.")


if __name__ == "__main__":
    sys.exit(main())

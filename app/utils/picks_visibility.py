from datetime import datetime, timezone

def mask_pick_if_not_started(player_name: str, game_start: datetime | None) -> str:
    """Return player_name if game has started, else 'LOCKED'."""
    if not player_name:
        return None
    if not game_start:
        return player_name  # If we can't find a game, show name by default
    now = datetime.now(timezone.utc)
    return player_name if now >= game_start else "LOCKED"
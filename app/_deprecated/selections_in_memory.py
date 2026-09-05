from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

router = APIRouter()

# In-memory mock DB for now. Replace with actual DB logic.
user_selections: dict[tuple[int, str], dict] = {}  # {(week, email): {selections, timestamp}}

class PlayerSelection(BaseModel):
    player_id: str
    player_name: str

class WeeklyPick(BaseModel):
    week: int
    userName: str  # email or user ID
    selections: Dict[str, PlayerSelection]  # keys: QB, RB, WR
    timestamp: Optional[str] = None

# Get users selected players for a week (why is this with api prefix and others are not?)
@router.get("/api/selections/{week}/{user}")
async def get_selection(week: int, user: str):
    key = (week, user.lower())
    if key in user_selections:
        return user_selections[key]
    return {"selections": {}, "timestamp": None}

# Write users selected players for the week into DB
@router.post("/api/selections")
async def submit_selection(pick: WeeklyPick):
    key = (pick.week, pick.userName.lower())
    user_selections[key] = {
        "selections": pick.selections,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {"message": "Selections saved", "data": user_selections[key]}

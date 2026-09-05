from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas
from datetime import datetime, timezone
from typing import Optional


# --- PLAYER FUNCTIONS ---
async def get_players_by_position(db: AsyncSession, position: str):
    stmt = select(models.Player).where(models.Player.position == position.upper())
    result = await db.execute(stmt)
    return result.scalars().all()

# --- WEEKLY PICK FUNCTIONS ---
async def get_all_picks(db: AsyncSession, season: int = None, league_id: int = None):
    stmt = select(models.WeeklyPick).options(joinedload(models.WeeklyPick.user))

    if season:
        stmt = stmt.where(models.WeeklyPick.season == season)
    if league_id:
        stmt = stmt.where(models.WeeklyPick.league_id == league_id)

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_pick_by_user_and_week(db: AsyncSession, user_email: str, week: int, season: int, league_id: int):
    stmt = select(models.WeeklyPick).where(
        models.WeeklyPick.user_email == user_email,
        models.WeeklyPick.week == week,
        models.WeeklyPick.season == season,
        models.WeeklyPick.league_id == league_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

def ensure_aware(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def create_or_update_pick(db: AsyncSession, pick: schemas.PickCreate):
    print(f"🔍 Attempting to create/update pick for {pick.user_email}, Week {pick.week}, Season {pick.season}, League {pick.league_id}")

    timestamp = ensure_aware(pick.timestamp)

    db_pick = await get_pick_by_user_and_week(
        db,
        user_email=pick.user_email,
        week=pick.week,
        season=pick.season,
        league_id=pick.league_id,
    )

    if db_pick:
        print("✏️ Pick already exists — updating existing entry")
        db_pick.qb = pick.qb
        db_pick.rb = pick.rb
        db_pick.wr = pick.wr
        db_pick.timestamp = timestamp
    else:
        print("🆕 No existing pick — creating new one")
        db_pick = models.WeeklyPick(
            **pick.model_dump(exclude={"timestamp"}),
            timestamp=timestamp
        )
        db.add(db_pick)

    try:
        await db.commit()
        await db.refresh(db_pick)
        print(f"✅ Pick saved: {db_pick}")
    except Exception as e:
        print(f"❌ Error committing pick to DB: {e}")
        raise

    return db_pick
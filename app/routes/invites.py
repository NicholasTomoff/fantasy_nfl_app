from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter()

import logging

logger = logging.getLogger("app.invite")
logging.basicConfig(level=logging.DEBUG)  # Adjust level as needed

# --------- Generate Invite Link ---------
@router.post("/generate-invite/{league_id}")
async def generate_invite(league_id: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logger.debug(f"🚀 generate_invite called with league_id={league_id}, current_user_id={current_user.id}")

    # Check that the league exists
    result = await db.execute(
        select(models.League).where(models.League.id == league_id)
    )
    league = result.unique().scalars().first()
    logger.debug(f"🔍 League query executed, league found: {league is not None}")
    if not league:
        logger.warning(f"⚠️ League with id {league_id} not found")
        raise HTTPException(status_code=404, detail="League not found.")

    # Restrict to league members only
    result = await db.execute(
        select(models.LeagueMember).where(
            models.LeagueMember.league_id == league_id,
            models.LeagueMember.user_id == current_user.id,
        )
    )
    membership = result.unique().scalars().first()
    logger.debug(f"🔍 Membership query executed, membership found: {membership is not None}")
    if not membership:
        logger.warning(f"⛔ User {current_user.id} is not a member of league {league_id}")
        raise HTTPException(status_code=403, detail="You must be a member of this league to invite others.")

    # Generate and store new invite token
    token = str(uuid4())
    logger.debug(f"🆕 Generated invite token: {token}")

    invite = models.LeagueInviteToken(
        token=token,
        league_id=league_id,
        created_at=datetime.utcnow()
    )
    db.add(invite)
    await db.commit()
    logger.debug(f"💾 Invite token committed to DB for league_id={league_id}")

    return {"invite_url": f"/join-league/{token}"}

# --------- Accept Invite Link ---------
@router.post("/join-league/{token}")
async def join_league_by_token(token: str, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    print(f"🔑 Attempting to join league with invite token: {token}")
    print(f"👤 Current user ID: {current_user.id}")

    # ✅ Look up invite
    result = await db.execute(
        select(models.LeagueInviteToken).where(models.LeagueInviteToken.token == token)
    )
    invite = result.unique().scalar_one_or_none()
    if not invite:
        print("❌ Invite token not found or expired.")
        raise HTTPException(status_code=404, detail="Invalid or expired invite link.")
    print(f"✅ Invite token found for league_id: {invite.league_id}")

    # ✅ Check if already a member
    result = await db.execute(
        select(models.LeagueMember).where(
            models.LeagueMember.league_id == invite.league_id,
            models.LeagueMember.user_id == current_user.id
        )
    )
    existing = result.unique().scalar_one_or_none()
    if existing:
        print("🔁 User is already a member of the league.")
        return {"message": "You are already a member of this league."}

    # ✅ Add user to league
    print(f"➕ Adding user {current_user.id} to league {invite.league_id}")
    print(f"🛠️ Creating membership for user={current_user.id}, league={invite.league_id}")
    
    membership = models.LeagueMember(
        league_id=invite.league_id,
        user_id=current_user.id
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    print(f"✅ Membership created with ID: {membership.id}")

    return {"message": "Successfully joined the league.", "league_id": invite.league_id}

# --------- Get Info About Invite Token (public) ---------
@router.get("/invite-info/{token}", response_model=schemas.LeagueOut)
async def get_invite_info(token: str, db: AsyncSession = Depends(get_db)):
    print(f"🔍 Checking invite token info: {token}")

    # ✅ Lookup invite token
    result = await db.execute(
        select(models.LeagueInviteToken).where(models.LeagueInviteToken.token == token)
    )
    invite = result.unique().scalar_one_or_none()
    if not invite:
        print("❌ Invalid or expired token.")
        raise HTTPException(status_code=404, detail="Invalid or expired invite link.")
    print(f"✅ Invite found for league ID: {invite.league_id}")

    # ✅ Lookup league details
    result = await db.execute(
        select(models.League).where(models.League.id == invite.league_id)
    )
    league = result.unique().scalar_one_or_none()
    if not league:
        print("❌ League not found for invite.")
        raise HTTPException(status_code=404, detail="League not found for invite.")

    print(f"📦 Returning league info for: {league.name}")
    return schemas.LeagueOut.from_orm(league)

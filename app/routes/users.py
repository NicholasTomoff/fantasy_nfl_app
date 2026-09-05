from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from passlib.context import CryptContext
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, create_access_token, pwd_context, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import os
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day token expiry

# Detect test database usage based on the DATABASE_URL in .env
DATABASE_URL = os.getenv("DATABASE_URL", "")
IS_TEST_DB = "test-fantasy" in DATABASE_URL  # Adjust as needed

# Create user info
@router.post("/signup", response_model=schemas.UserLoginResponse)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info("🔐 Signup attempt for email: %s", user.email)

    result = await db.execute(select(models.User).filter(models.User.email == user.email))
    existing_user = result.unique().scalars().first()
    if existing_user:
        logger.warning("⚠️ Email already registered: %s", user.email)
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password)
    db.add(new_user)
    await db.flush()

    logger.info("✅ New user created with ID: %s", new_user.id)

    # Test league auto-join
    logger.info("🧪 IS_TEST_DB = %s", IS_TEST_DB)
    if IS_TEST_DB:
        test_league_ids = [2, 3, 4]
        for league_id in test_league_ids:
            logger.info("➡️ Attempting to join test league: %s", league_id)
            db.add(models.LeagueMember(user_id=new_user.id, league_id=league_id))

    await db.commit()
    await db.refresh(new_user)

    result = await db.execute(
        select(models.User)
        .options(joinedload(models.User.memberships).joinedload(models.LeagueMember.league))
        .where(models.User.id == new_user.id)
    )
    fresh_user = result.unique().scalars().first()

    if not fresh_user:
        logger.error("❌ Failed to reload user after commit")
        raise HTTPException(status_code=500, detail="User creation failed")

    leagues = [
        {"id": league.id, "name": league.name}
        for league in fresh_user.leagues if league
    ]

    logger.info("📦 User leagues after signup: %s", leagues)

    token = create_access_token(
        data={"sub": fresh_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "user": {
            "id": fresh_user.id,
            "email": fresh_user.email,
            "name": fresh_user.name,
            "leagues": leagues
        },
        "token": token,
    }

# Authenticate user and load leagues user is a member of (post route)
@router.post("/login", response_model=schemas.UserLoginResponse)
async def login_user(user_credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(models.User)
        .options(
            joinedload(models.User.memberships).joinedload(models.LeagueMember.league),
            joinedload(models.User.hosted_leagues),
        )
        .filter(models.User.email == user_credentials.email)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()


    if not user:
        logger.warning("❌ Login failed: no user found for email=%s", user_credentials.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Debug lengths and previews before calling passlib
    plain_pw = user_credentials.password
    hashed_pw = user.hashed_password

    logger.info("🔑 Attempt login for %s", user_credentials.email)
    logger.info("   plain_pw length=%d, preview=%s", len(plain_pw.encode("utf-8")), repr(plain_pw)[:50])
    logger.info("   hashed_pw length=%d, preview=%s", len(hashed_pw) if hashed_pw else 0, hashed_pw[:50] if hashed_pw else None)

    try:
        if not pwd_context.verify(plain_pw, hashed_pw):
            logger.warning("❌ Password verify failed for email=%s", user_credentials.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error("💥 Exception during verify: %s", e, exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid credentials")


    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    # Load memberships async if needed
    leagues = [
        {"id": m.league.id, "name": m.league.name, "season": m.league.season_year}
        for m in user.memberships
    ]

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "leagues": leagues,
        },
        "token": token,
    }

# Get authenticated user info
@router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    print("📥 /me route called")

    # Ensure full user data with memberships → leagues is loaded
    stmt = (
        select(models.User)
        .options(
            joinedload(models.User.memberships).joinedload(models.LeagueMember.league)
        )
        .where(models.User.id == current_user.id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    league_data = [
        {
            "id": lm.league.id,
            "name": lm.league.name,
            "season": lm.league.season_year,
        }
        for lm in user.memberships
        if lm.league is not None
    ]

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "leagues": league_data,
    }

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str

# Request of forgotten password by user (post route)
@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest = Body(...), db: AsyncSession = Depends(get_db)):
    # Security: Do not reveal if email exists or not
    return {"detail": "If the email exists, you may reset your password."}

# Request to reset password (forgot password) by user (generate new password for user)
@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest = Body(...), db: AsyncSession = Depends(get_db)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    stmt = (
        select(models.User)
        .options(joinedload(models.User.memberships).joinedload(models.LeagueMember.league))
        .filter(models.User.email == payload.email)
    )
    result = await db.execute(select(models.User).filter(models.User.email == payload.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed = pwd_context.hash(payload.new_password)
    user.hashed_password = hashed
    await db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    leagues = [
        {"id": m.league.id, "name": m.league.name, "season": m.league.season_year}
        for m in user.memberships
    ]
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "leagues": leagues,
        },
        "token": token,
    }

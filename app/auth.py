# auth.py
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models import User, LeagueMember
from app.database import get_db
from app.schemas import UserOut

# -------------------------------
# Configuration
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# Password utilities
# -------------------------------
def get_password_hash(password: str) -> str:
    """
    Hash a password, truncating to 72 bytes to satisfy bcrypt.
    """
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash. Truncates to 72 bytes to prevent bcrypt errors.
    """
    return pwd_context.verify(plain_password[:72], hashed_password)

# -------------------------------
# JWT utilities
# -------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------------
# Dependency to get current user
# -------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    # Decode JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch user with memberships
    stmt = (
        select(User)
        .options(joinedload(User.memberships).joinedload(LeagueMember.league))
        .filter(User.email == email)
    )
    result = await db.execute(stmt)
    user = result.scalars().unique().one_or_none()

    if not user:
        raise credentials_exception

    # Build leagues list
    leagues = [
        {"id": m.league.id, "name": m.league.name}
        for m in user.memberships if m.league
    ]

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        leagues=leagues
    )

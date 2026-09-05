"""
Season-scoped league membership.

Two tables answer two different questions:

  league_members         -- the permanent roster: "has ever played in this league".
                            Never deleted, which is what keeps a departed member's
                            picks, scores and podium finishes resolvable.
  league_season_members  -- "is this person playing in season N".

Everything that iterates players for a season (scoring, standings) should go
through here rather than reading league_members directly.
"""

from sqlalchemy import and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, LeagueMember, LeagueSeasonMember

# A member who has not answered yet is still scored. Only an explicit "out"
# removes someone from a season -- far better to include someone who forgot to
# click than to silently drop them from the standings.
ACTIVE_STATUSES = ("in", "pending")


async def get_active_member_emails(
    db: AsyncSession, league_id: int, season_year: int
) -> set[str]:
    """
    Emails of the members playing this league in this season.

    One query: outer-join the roster to this season's check-in rows. A member
    with no row for the season (either because the season was never opened, or
    because they joined after it was) reads as NULL and counts as active -- so
    behaviour is unchanged until someone is explicitly marked out.
    """
    stmt = (
        select(User.email, LeagueSeasonMember.status)
        .select_from(LeagueMember)
        .join(User, User.id == LeagueMember.user_id)
        .outerjoin(
            LeagueSeasonMember,
            and_(
                LeagueSeasonMember.user_id == LeagueMember.user_id,
                LeagueSeasonMember.league_id == LeagueMember.league_id,
                LeagueSeasonMember.season_year == season_year,
            ),
        )
        .filter(LeagueMember.league_id == league_id)
    )
    rows = (await db.execute(stmt)).all()
    return {
        email for email, status in rows
        if status is None or status in ACTIVE_STATUSES
    }


async def get_roster_emails(db: AsyncSession, league_id: int) -> set[str]:
    """Every member who has ever been in this league, regardless of season."""
    stmt = (
        select(User.email)
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .filter(LeagueMember.league_id == league_id)
    )
    return set((await db.execute(stmt)).scalars().all())


async def season_is_opened(db: AsyncSession, league_id: int, season_year: int) -> bool:
    """True once check-in rows exist for this league/season."""
    stmt = (
        select(LeagueSeasonMember.id)
        .filter(
            LeagueSeasonMember.league_id == league_id,
            LeagueSeasonMember.season_year == season_year,
        )
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first() is not None

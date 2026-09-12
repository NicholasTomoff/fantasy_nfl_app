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

from datetime import datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, LeagueMember, LeagueSeasonMember, NFLGame

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


async def mark_in_for_season(
    db: AsyncSession, league_id: int, season_year: int, user_id: int
) -> None:
    """
    Record a member as playing this season.

    Accepting an invite is itself an answer, so someone who joins should not
    land on "no answer yet" and have to confirm a second time. Existing rows are
    left alone: if they had already said they were sitting out, re-joining
    should not silently overturn that.
    """
    existing = (await db.execute(
        select(LeagueSeasonMember).filter_by(
            league_id=league_id, season_year=season_year, user_id=user_id
        )
    )).scalars().first()
    if existing:
        return

    db.add(
        LeagueSeasonMember(
            league_id=league_id,
            season_year=season_year,
            user_id=user_id,
            status="in",
            responded_at=datetime.utcnow(),
        )
    )


# Week 1 is an opt-in grace period: everyone gets the full opening week to say
# whether they are playing. Check-in closes once Week 1 is finalised, using the
# same 12-hour-after-the-last-game rule the scoring engine uses to decide a week
# is done (see app/utils/season.get_current_finalized_week).
WEEK_1_GRACE_HOURS = 12


async def check_in_deadline(db: AsyncSession, season_year: int):
    """
    When check-in closes: 12 hours after the last Week 1 regular-season game.
    Returns None if the season has no Week 1 games, meaning no deadline yet.
    """
    last_week1_game = (await db.execute(
        select(func.max(NFLGame.date)).filter(
            NFLGame.season == season_year,
            NFLGame.stage == "Regular Season",
            NFLGame.week == "Week 1",
        )
    )).scalar_one_or_none()

    if last_week1_game is None:
        return None
    return last_week1_game + timedelta(hours=WEEK_1_GRACE_HOURS)


async def check_in_is_open(db: AsyncSession, season_year: int) -> bool:
    """
    Open through the whole of Week 1, not just up to the first kickoff.

    Closing at the opening game left anyone who had not clicked by Thursday
    night with no way to opt in, which is the opposite of the intent: a member
    who has not answered is still scored, so the window exists to let people
    opt OUT, and they deserve the full week to do it.
    """
    deadline = await check_in_deadline(db, season_year)
    if deadline is None:
        return True
    return datetime.utcnow() < deadline

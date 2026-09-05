# /services/streak_history_service.py

from sqlalchemy import select, func
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    WeeklyScore,
    User,
    League,
    StreakSeasonHistory,
)


# -----------------------------------------
# Utility: longest consecutive True values
# -----------------------------------------
def _longest_consecutive(boolean_list):
    max_streak = 0
    current = 0

    for value in boolean_list:
        if value:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0

    return max_streak


# -----------------------------------------
# Calculate Best Triple Start
# -----------------------------------------
async def _calculate_best_triple_start(session: AsyncSession, league_id, season):

    result = await session.execute(
        select(WeeklyScore.user_email)
        .where(
            WeeklyScore.league_id == league_id,
            WeeklyScore.season == season,
        )
        .distinct()
    )
    users = result.scalars().all()

    max_start = 0
    max_user_id = None

    for email in users:

        scores_result = await session.execute(
            select(WeeklyScore)
            .where(
                WeeklyScore.league_id == league_id,
                WeeklyScore.season == season,
                WeeklyScore.user_email == email,
            )
            .order_by(WeeklyScore.week)
        )
        scores = scores_result.scalars().all()

        count = 0
        for s in scores:
            if s.all_positions_bonus and s.all_positions_bonus > 0:
                count += 1
            else:
                break

        if count > max_start:
            max_start = count

            user_result = await session.execute(
                select(User).where(User.email == email)
            )
            user = user_result.scalar_one_or_none()
            max_user_id = user.id if user else None

    return max_start, max_user_id


# -----------------------------------------
# Calculate Longest Triple Streak
# -----------------------------------------
async def _calculate_longest_triple(session: AsyncSession, league_id, season):

    result = await session.execute(
        select(WeeklyScore.user_email)
        .where(
            WeeklyScore.league_id == league_id,
            WeeklyScore.season == season,
        )
        .distinct()
    )
    users = result.scalars().all()

    max_streak = 0
    max_user_id = None

    for email in users:

        scores_result = await session.execute(
            select(WeeklyScore)
            .where(
                WeeklyScore.league_id == league_id,
                WeeklyScore.season == season,
                WeeklyScore.user_email == email,
            )
            .order_by(WeeklyScore.week)
        )
        scores = scores_result.scalars().all()

        values = [
            bool(s.all_positions_bonus and s.all_positions_bonus > 0)
            for s in scores
        ]

        streak = _longest_consecutive(values)

        if streak > max_streak:
            max_streak = streak

            user_result = await session.execute(
                select(User).where(User.email == email)
            )
            user = user_result.scalar_one_or_none()
            max_user_id = user.id if user else None

    return max_streak, max_user_id


# -----------------------------------------
# Calculate Longest Positional Streak
# -----------------------------------------
async def _calculate_longest_position(session: AsyncSession, league_id, season, position):

    result = await session.execute(
        select(WeeklyScore.user_email)
        .where(
            WeeklyScore.league_id == league_id,
            WeeklyScore.season == season,
        )
        .distinct()
    )
    users = result.scalars().all()

    max_streak = 0

    for email in users:

        scores_result = await session.execute(
            select(WeeklyScore)
            .where(
                WeeklyScore.league_id == league_id,
                WeeklyScore.season == season,
                WeeklyScore.user_email == email,
            )
            .order_by(WeeklyScore.week)
        )
        scores = scores_result.scalars().all()

        if position == "QB":
            values = [s.qb_streak > 0 for s in scores]
        elif position == "RB":
            values = [s.rb_streak > 0 for s in scores]
        else:
            values = [s.wr_streak > 0 for s in scores]

        streak = _longest_consecutive(values)
        max_streak = max(max_streak, streak)

    return max_streak


# -----------------------------------------
# Calculate Most Triples In Season
# -----------------------------------------
async def _calculate_most_triples(session: AsyncSession, league_id, season):

    result = await session.execute(
        select(WeeklyScore.user_email)
        .where(
            WeeklyScore.league_id == league_id,
            WeeklyScore.season == season,
        )
        .distinct()
    )
    users = result.scalars().all()

    max_total = 0
    max_user_id = None

    for email in users:

        total_result = await session.execute(
            select(func.count(WeeklyScore.id)).where(
                WeeklyScore.league_id == league_id,
                WeeklyScore.season == season,
                WeeklyScore.user_email == email,
                WeeklyScore.all_positions_bonus > 0,
            )
        )
        total = total_result.scalar() or 0

        if total > max_total:
            max_total = total

            user_result = await session.execute(
                select(User).where(User.email == email)
            )
            user = user_result.scalar_one_or_none()
            max_user_id = user.id if user else None

    return max_total, max_user_id


# -----------------------------------------
# MAIN ENTRY FUNCTION
# -----------------------------------------
async def _calculate_podium(session: AsyncSession, league_id, season):
    """
    Final finishing order for a season, as (champion, runner_up, third) user ids.

    WeeklyScore.total_points is cumulative -- each week carries the previous
    total forward -- so a user's season total is simply their highest weekly
    value. Pass league_id=None to rank across every league (the global row).

    Returns None in any place that has no user (e.g. a two-person league).
    """
    stmt = (
        select(User.id, func.max(WeeklyScore.total_points).label("pts"))
        .join(WeeklyScore, WeeklyScore.user_email == User.email)
        .where(WeeklyScore.season == season)
    )
    if league_id is not None:
        stmt = stmt.where(WeeklyScore.league_id == league_id)

    stmt = (
        stmt.group_by(User.id)
        .order_by(func.max(WeeklyScore.total_points).desc(), User.id)
        .limit(3)
    )
    ids = [r[0] for r in (await session.execute(stmt)).all()]
    ids += [None] * (3 - len(ids))
    return ids[0], ids[1], ids[2]


async def generate_streak_history_for_season(season: int, session: AsyncSession):

    league_result = await session.execute(select(League))
    leagues = league_result.scalars().all()

    for league in leagues:

        league_id = league.id

        member_result = await session.execute(
            select(WeeklyScore.user_email)
            .where(
                WeeklyScore.league_id == league_id,
                WeeklyScore.season == season,
            )
            .distinct()
        )
        member_count = len(member_result.scalars().all())

        best_start, best_start_user = await _calculate_best_triple_start(session, league_id, season)
        longest_triple, longest_triple_user = await _calculate_longest_triple(session, league_id, season)

        longest_qb = await _calculate_longest_position(session, league_id, season, "QB")
        longest_rb = await _calculate_longest_position(session, league_id, season, "RB")
        longest_wr = await _calculate_longest_position(session, league_id, season, "WR")

        most_triples, most_triples_user = await _calculate_most_triples(session, league_id, season)
        champion_id, runner_up_id, third_place_id = await _calculate_podium(session, league_id, season)

        existing_result = await session.execute(
            select(StreakSeasonHistory).where(
                StreakSeasonHistory.league_id == league_id,
                StreakSeasonHistory.season == season,
                StreakSeasonHistory.scope == "league",
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            continue

        row = StreakSeasonHistory(
            scope="league",
            league_id=league_id,
            season=season,
            member_count=member_count,
            champion_id=champion_id,
            runner_up_id=runner_up_id,
            third_place_id=third_place_id,
            best_triple_start=best_start,
            best_triple_start_user_id=best_start_user,
            longest_triple_streak=longest_triple,
            longest_triple_user_id=longest_triple_user,
            longest_qb_streak=longest_qb,
            longest_rb_streak=longest_rb,
            longest_wr_streak=longest_wr,
            most_triples_in_season=most_triples,
            most_triples_user_id=most_triples_user,
            created_at=datetime.utcnow(),
        )

        session.add(row)

    await session.commit()

    # -----------------------------------------
    # GLOBAL ROW
    # -----------------------------------------

    global_check = await session.execute(
        select(StreakSeasonHistory).where(
            StreakSeasonHistory.season == season,
            StreakSeasonHistory.scope == "global",
        )
    )
    existing_global = global_check.scalar_one_or_none()

    if existing_global:
        return

    league_rows_result = await session.execute(
        select(StreakSeasonHistory).where(
            StreakSeasonHistory.season == season,
            StreakSeasonHistory.scope == "league",
        )
    )
    league_rows = league_rows_result.scalars().all()

    if not league_rows:
        return

    g_champion, g_runner_up, g_third = await _calculate_podium(session, None, season)

    global_row = StreakSeasonHistory(
        scope="global",
        league_id=None,
        season=season,
        member_count=sum(r.member_count for r in league_rows),
        champion_id=g_champion,
        runner_up_id=g_runner_up,
        third_place_id=g_third,
        best_triple_start=max(r.best_triple_start for r in league_rows),
        longest_triple_streak=max(r.longest_triple_streak for r in league_rows),
        longest_qb_streak=max(r.longest_qb_streak for r in league_rows),
        longest_rb_streak=max(r.longest_rb_streak for r in league_rows),
        longest_wr_streak=max(r.longest_wr_streak for r in league_rows),
        most_triples_in_season=max(r.most_triples_in_season for r in league_rows),
        created_at=datetime.utcnow(),
    )

    session.add(global_row)
    await session.commit()

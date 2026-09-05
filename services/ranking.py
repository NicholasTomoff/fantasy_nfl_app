from sqlalchemy import func, select
from app.models import WeeklyScore, AllPositionStreak


def assign_ranks(rows):
    """
    Assign ranks with ties.
    rows must be sorted by points DESC.
    Returns list of dicts: {rank, row}
    """
    ranked = []
    current_rank = 0
    prev_points = None
    items_seen = 0

    for row in rows:
        items_seen += 1
        # Only update rank when points change
        if row.points != prev_points:
            current_rank = items_seen
        ranked.append({"rank": current_rank, "row": row})
        prev_points = row.points

    return ranked


async def get_user_ranks(db, user_email: str, league_id: int, week: int, season: int):
    normalized_user_email = user_email.strip().lower()

    # 1. Global totals: sum points grouped by user_email + league_id
    stmt_global = (
        select(
            WeeklyScore.user_email,
            WeeklyScore.league_id,
            func.sum(WeeklyScore.total_points).label("points")
        )
        .filter(
            WeeklyScore.season == season,
            WeeklyScore.week == week
        )
        .group_by(WeeklyScore.user_email, WeeklyScore.league_id)
        .order_by(func.sum(WeeklyScore.total_points).desc())
    )
    result_global = await db.execute(stmt_global)
    global_totals = result_global.all()

    print(f"[DEBUG] Global totals count (Week {week}): {len(global_totals)}")
    ranked_global = assign_ranks(global_totals)
    for r in ranked_global[:5]:
        print(f"Global Rank {r['rank']}: user={r['row'].user_email} "
              f"league={r['row'].league_id} points={r['row'].points}")

    global_rank = next(
        (
            r["rank"]
            for r in ranked_global
            if r["row"].user_email.strip().lower() == normalized_user_email
            and r["row"].league_id == league_id
        ),
        "-"
    )

    # 2. League totals: users in this league only
    stmt_league_users = (
        select(WeeklyScore.user_email)
        .filter(
            WeeklyScore.league_id == league_id,
            WeeklyScore.season == season,
            WeeklyScore.week == week
        )
        .distinct()
    )
    result_league_users = await db.execute(stmt_league_users)
    league_user_emails = [email[0].strip().lower() for email in result_league_users.all()]

    league_totals = [
        u for u in global_totals
        if u.user_email.strip().lower() in league_user_emails and u.league_id == league_id
    ]

    print(f"[DEBUG] League totals count (Week {week}, League {league_id}): {len(league_totals)}")
    ranked_league = assign_ranks(league_totals)
    for r in ranked_league[:5]:
        print(f"League Rank {r['rank']}: user={r['row'].user_email} points={r['row'].points}")

    league_rank = next(
        (
            r["rank"]
            for r in ranked_league
            if r["row"].user_email.strip().lower() == normalized_user_email
        ),
        "-"
    )

    # 3. Current streak points for this user
    stmt_streak = (
        select(AllPositionStreak.current_streak)
        .filter(
            AllPositionStreak.user_email == normalized_user_email,
            AllPositionStreak.league_id == league_id,
            AllPositionStreak.last_updated_week == week
        )
    )
    result_streak = await db.execute(stmt_streak)
    current_streak_obj = result_streak.first()
    current_streak_points = current_streak_obj.current_streak if current_streak_obj else 0

    return {
        "global_rank": global_rank,
        "league_rank": league_rank,
        "current_streak": current_streak_points,
    }

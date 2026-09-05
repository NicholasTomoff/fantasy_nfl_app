import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models import WeeklyPick, PlayerGameStat, WeeklyScore, PositionStreak, AllPositionStreak, NFLGame, Player, LeagueMember, User
from app.database import async_session
from app.utils.membership import get_active_member_emails
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def get_previous_week_score(db: AsyncSession, email: str, week: int, season: int, league_id: int) -> Optional[WeeklyScore]:
    if week <= 1:
        print(f"⏮️ Week {week} - no previous week to load score from.")
        return None
    result = await db.execute(
        select(WeeklyScore).filter_by(user_email=email, week=week-1, season=season, league_id=league_id)
    )
    prev_score = result.scalars().first()
    print(f"🔙 Loaded previous week {week-1} score for {email}: {prev_score}")
    return prev_score

async def update_position_streak(db: AsyncSession, email: str, pos: str, hit: bool, week: int, league_id: int, initial_streak: int = 0):
    pos_upper = pos.upper()
    result = await db.execute(
        select(PositionStreak).filter_by(user_email=email, position=pos_upper, league_id=league_id)
    )
    streak_obj = result.scalars().first()

    if streak_obj and streak_obj.last_updated_week == week:
        print(f"⏭️ {pos_upper} streak already updated for week {week}, skipping. Current streak: {streak_obj.current_streak}")
        return streak_obj.current_streak, 0  # already updated, no points

    # Start streak count from previous weekly score streak if no PositionStreak found or it's stale
    current_streak = initial_streak
    print(f"🔄 {pos_upper} initial streak (from previous week score): {initial_streak}")

    if hit:
        pos_points = 1 + current_streak
        current_streak += 1
        print(f"✅ {pos_upper} HIT! Streak incremented to {current_streak}, points awarded: {pos_points}")
    else:
        pos_points = 0
        current_streak = 0
        print(f"❌ {pos_upper} MISS. Streak reset to 0, points awarded: {pos_points}")

    if streak_obj:
        streak_obj.current_streak = current_streak
        streak_obj.last_updated_week = week
        print(f"✏️ Updated existing {pos_upper} PositionStreak to {current_streak} for week {week}")
    else:
        new_streak = PositionStreak(
            user_email=email,
            position=pos_upper,
            current_streak=current_streak,
            last_updated_week=week,
            league_id=league_id
        )
        db.add(new_streak)
        await db.flush()
        print(f"💾 Created new {pos_upper} PositionStreak with streak {current_streak} for week {week}")

    return current_streak, pos_points

# ...
async def update_all_position_streak(db: AsyncSession, email: str, all_hit: bool, week: int, league_id: int, initial_all_streak: int = 0):
    result = await db.execute(
        select(AllPositionStreak).filter_by(user_email=email, league_id=league_id)
    )
    all_streak = result.scalars().first()

    if all_streak and all_streak.last_updated_week == week:
        logger.debug(f"⏭️ All-position streak already updated for {email} week {week}: {all_streak.current_streak}")
        return all_streak.current_streak, 0

    current_all_streak = initial_all_streak
    all_bonus = 0

    if all_hit:
        current_all_streak += 1
        all_bonus = 5 * current_all_streak
        logger.debug(f"🎯 All positions HIT for {email} week {week}: streak {current_all_streak}, bonus {all_bonus}")
    else:
        logger.debug(f"❌ All positions MISS for {email} week {week}: streak reset to 0")
        current_all_streak = 0

    if all_streak:
        all_streak.current_streak = current_all_streak
        all_streak.last_updated_week = week
    else:
        new_all_streak = AllPositionStreak(
            user_email=email,
            current_streak=current_all_streak,
            last_updated_week=week,
            league_id=league_id
        )
        db.add(new_all_streak)

    await db.flush()  # ✅ <-- always flush

    return current_all_streak, all_bonus

async def get_player_stat(db: AsyncSession, player_id: int, game_ids: list[int]):
    result = await db.execute(
        select(PlayerGameStat).filter(
            and_(
                PlayerGameStat.player_id == player_id,
                PlayerGameStat.game_id.in_(game_ids)
            )
        )
    )
    stat = result.scalars().first()
    print(f"📊 Retrieved stats for player_id {player_id}: {stat}")
    return stat

def evaluate_hit(pos: str, stat, player_position: str = None) -> bool:
    """
    Evaluate if a player 'hit' their yard/TD thresholds.
    WR includes TE here.
    """
    pos = pos.lower()
    
    rushing_yards = stat.rushing_yards or 0
    receiving_yards = stat.receiving_yards or 0
    rushing_tds = stat.rushing_tds or 0
    receiving_tds = stat.receiving_tds or 0
    passing_yards = stat.passing_yards or 0
    passing_tds = stat.passing_tds or 0

    total_yards = rushing_yards + receiving_yards
    total_tds = rushing_tds + receiving_tds + passing_tds

    if pos == "qb":
        hit = passing_yards >= 300 or total_tds >= 2 or rushing_yards >= 100 or total_yards >= 125
    else:  # RB / WR
        # Treat TE as WR
        if player_position in ["TE", "WR"]:
            hit = rushing_yards >= 100 or receiving_yards >= 100 or total_yards >= 125 or total_tds >= 1
        else:  # RB
            hit = rushing_yards >= 100 or receiving_yards >= 100 or total_yards >= 125 or total_tds >= 1
    
    return hit

async def score_week_with_session(db: AsyncSession, week: int, season: int, league_id: int):
    print(f"🏈 Scoring Week {week} for league {league_id}, season {season}...")

    # --- Members playing this league THIS season (falls back to the full
    #     roster when the season was never opened for check-in) ---
    all_users = await get_active_member_emails(db, league_id, season)

    # Load all picks for this week and league
    result = await db.execute(select(WeeklyPick).filter_by(week=week, season=season, league_id=league_id))
    picks = result.scalars().all()

    # Drop picks belonging to members who are sitting this season out. Their
    # pick rows stay in the table; they simply are not scored or ranked.
    skipped = [p.user_email for p in picks if p.user_email not in all_users]
    if skipped:
        print(f"🚫 Ignoring picks from members not active this season: {sorted(set(skipped))}")
    picks = [p for p in picks if p.user_email in all_users]
    print(f"👥 Found {len(picks)} picks to score.")

    # ==================================================
    # >>> ADDITION START: handle users with NO picks
    # ==================================================

    # Users who DID submit picks this week
    picked_users = {p.user_email for p in picks}

    # Users missing this week
    users_without_picks = all_users - picked_users

    carried_users = []  # debug tracking

    print(f"👥 Found {len(users_without_picks)} users this week without picks: {users_without_picks}")

    for email in users_without_picks:
        print(f"🔍 Processing carry-forward for {email} week {week} league {league_id}...")
        prev = await get_previous_week_score(db, email, week, season, league_id)

        if not prev:
            print(f"🛟 No previous score to carry for {email}, skipping.")
            continue

        # Avoid duplicate scoring
        result = await db.execute(
            select(WeeklyScore).filter_by(
                user_email=email,
                week=week,
                season=season,
                league_id=league_id,
            )
        )
        exists = result.scalars().first()
        if exists:
            print(f"⏭️ WeeklyScore already exists for {email} week {week}, skipping carry-forward")
            continue

       # --- Carry forward ---
        print(f"💾 Creating carry-forward WeeklyScore for {email} week {week}, prev points {prev.total_points}")
        carried_score = WeeklyScore(
            user_email=email,
            week=week,
            season=season,
            league_id=league_id,
            total_points=prev.total_points or 0,  # ensure not None
            qb_points=0,
            rb_points=0,
            wr_points=0,
            qb_streak=0,
            rb_streak=0,
            wr_streak=0,
            all_positions_hit=False,
            all_positions_bonus=0,
        )
        db.add(carried_score)
        await db.flush()  # 🔥 important in async context
        carried_users.append(email)
        print(f"✅ Carry-forward row added for {email}, prev points {prev.total_points}")

    # --- DEBUG: show which users got carry-forward ---
    if carried_users:
        print(f"🛟 Carry-forward rows added for users: {carried_users}")
    else:
        print("🛟 No carry-forward users for this week.")

    await db.commit()
    print("💾 Carry-forward commit completed.")

    # ==================================================
    # <<< ADDITION END
    # ==================================================
    
    # Load NFL games for this week
    result = await db.execute(select(NFLGame).filter(NFLGame.week == f"Week {week}", NFLGame.season == season))
    nfl_games = result.scalars().all()
    if not nfl_games:
        print(f"⚠️ No NFL games found for Week {week}, cannot score.")
        return
    game_ids = [g.id for g in nfl_games]

    for pick in picks:
        email = pick.user_email
        print(f"\n🔍 Scoring for user: {email}")

        # Previous week's score
        previous_score = await get_previous_week_score(db, email, week, season, league_id)
        prev_qb_streak = previous_score.qb_streak if previous_score else 0
        prev_rb_streak = previous_score.rb_streak if previous_score else 0
        prev_wr_streak = previous_score.wr_streak if previous_score else 0
        prev_all_streak = previous_score.all_positions_bonus // 5 if previous_score and previous_score.all_positions_bonus else 0
        previous_total_points = previous_score.total_points if previous_score else 0

        print(f"⏮️ Previous total points: {previous_total_points}")
        print(f"⏮️ Previous streaks — QB: {prev_qb_streak}, RB: {prev_rb_streak}, WR: {prev_wr_streak}, All: {prev_all_streak}")

        # Check if position streaks already updated
        result = await db.execute(select(PositionStreak).filter_by(user_email=email, league_id=league_id))
        pos_streaks = result.scalars().all()
        updated_positions = [ps.position for ps in pos_streaks if ps.last_updated_week == week]
        if set(updated_positions) == {"QB", "RB", "WR"}:
            print("⏭️ All positions already updated for this week, skipping user.")
            continue

        total_points = previous_total_points
        score_breakdown = {}
        all_hit = True

        for pos in ["qb", "rb", "wr"]:
            player_id_raw = getattr(pick, pos)
            if not player_id_raw:
                print(f"⚠️ No player selected for {pos.upper()}, setting points and streak to 0.")
                all_hit = False
                score_breakdown[f"{pos}_points"] = 0
                score_breakdown[f"{pos}_streak"] = 0
                continue
            try:
                player_id = int(player_id_raw)
            except ValueError:
                print(f"🚫 Invalid player_id {player_id_raw} for {pos.upper()}, setting points and streak to 0.")
                all_hit = False
                score_breakdown[f"{pos}_points"] = 0
                score_breakdown[f"{pos}_streak"] = 0
                continue

            # --- FETCH REAL POSITION (to handle TE as WR) ---
            result = await db.execute(select(Player.position).filter_by(player_id=player_id))
            player_pos = result.scalars().first()

            stat = await get_player_stat(db, player_id, game_ids)
            if not stat:
                print(f"⚠️ No stats found for player {player_id} in {pos.upper()}, points and streak set to 0.")
                all_hit = False
                score_breakdown[f"{pos}_points"] = 0
                score_breakdown[f"{pos}_streak"] = 0
                continue

            # --- EVALUATE HIT (with player_pos) ---
            hit = evaluate_hit(pos, stat, player_position=player_pos)

            # Pass previous streak baseline
            if pos == "qb":
                initial_streak = prev_qb_streak
            elif pos == "rb":
                initial_streak = prev_rb_streak
            else:
                initial_streak = prev_wr_streak

            current_streak, pos_points = await update_position_streak(
                db, email, pos, hit, week, league_id, initial_streak=initial_streak
            )

            score_breakdown[f"{pos}_points"] = pos_points
            score_breakdown[f"{pos}_streak"] = current_streak
            total_points += pos_points

            if pos_points == 0:
                all_hit = False

        # Update all-position streak
        current_all_streak, all_bonus = await update_all_position_streak(
            db, email, all_hit, week, league_id, initial_all_streak=prev_all_streak
        )
        total_points += all_bonus

        print(f"🧮 Total points for user {email}: {total_points}")
        print(f"💥 Breakdown: QB pts {score_breakdown['qb_points']} (streak {score_breakdown['qb_streak']}), "
              f"RB pts {score_breakdown['rb_points']} (streak {score_breakdown['rb_streak']}), "
              f"WR pts {score_breakdown['wr_points']} (streak {score_breakdown['wr_streak']}), "
              f"All-pos bonus: {all_bonus}")

        # Save or update WeeklyScore
        result = await db.execute(select(WeeklyScore).filter_by(user_email=email, week=week, season=season, league_id=league_id))
        existing_score = result.scalars().first()

        if existing_score:
            print(f"✏️ Updating WeeklyScore for {email} week {week}")
            existing_score.total_points = total_points
            existing_score.qb_points = score_breakdown.get("qb_points", 0)
            existing_score.qb_streak = score_breakdown.get("qb_streak", 0)
            existing_score.rb_points = score_breakdown.get("rb_points", 0)
            existing_score.rb_streak = score_breakdown.get("rb_streak", 0)
            existing_score.wr_points = score_breakdown.get("wr_points", 0)
            existing_score.wr_streak = score_breakdown.get("wr_streak", 0)
            existing_score.all_positions_hit = all_hit
            existing_score.all_positions_bonus = all_bonus
        else:
            print(f"💾 Creating new WeeklyScore for {email} week {week}")
            new_score = WeeklyScore(
                user_email=email,
                week=week,
                season=season,
                league_id=league_id,
                total_points=total_points,
                all_positions_hit=all_hit,
                all_positions_bonus=all_bonus,
                qb_points=score_breakdown.get("qb_points", 0),
                qb_streak=score_breakdown.get("qb_streak", 0),
                rb_points=score_breakdown.get("rb_points", 0),
                rb_streak=score_breakdown.get("rb_streak", 0),
                wr_points=score_breakdown.get("wr_points", 0),
                wr_streak=score_breakdown.get("wr_streak", 0),
            )
            db.add(new_score)
            await db.flush()

    await db.commit()
    print(f"✅ Finished scoring week {week} for league {league_id}.")

async def score_week(week: int, season: int, league_id: int):
    async with async_session() as db:
        try:
            await score_week_with_session(db, week, season, league_id)
        except Exception as e:
            await db.rollback()
            print(f"❌ Error during scoring: {e}")

async def project_max_points(league_id: int, currentFinalizedWeek: int, season: int):
    """
    Project maximum possible points for all league members assuming every future week
    (currentFinalizedWeek+1 through week 18) is a triple-hit and positional streaks
    increment accordingly.
    """

    if currentFinalizedWeek >= 18:
        raise HTTPException(
            status_code=400,
            detail="currentFinalizedWeek must be < 18 to project future weeks"
        )

    projected_end_week = 18
    weeks_to_project = list(range(currentFinalizedWeek + 1, projected_end_week + 1))

    async with async_session() as db:  
        # Get distinct list of users from WeeklyPick (league context)
        q = await db.execute(
            select(WeeklyPick.user_email).filter_by(league_id=league_id, season=season).distinct()
        )
        users = q.scalars().all() 

        results = []

        for email in users:

            # Load weekly score for finalized week
            ws_q = await db.execute(
                select(WeeklyScore).filter_by(
                    user_email=email,
                    week=currentFinalizedWeek,
                    season=season,
                    league_id=league_id
                )
            )
            finalized_score = ws_q.scalars().first()

            current_total_points = 0
            qb_streak = rb_streak = wr_streak = 0
            all_streak = 0

            if finalized_score:
                current_total_points = finalized_score.total_points or 0

                qb_streak = finalized_score.qb_streak or 0
                rb_streak = finalized_score.rb_streak or 0
                wr_streak = finalized_score.wr_streak or 0

                # all_positions_bonus = 5 * streak
                if finalized_score.all_positions_bonus:
                    all_streak = finalized_score.all_positions_bonus // 5

            else:
                # Fallback to PositionStreak + AllPositionStreak tables
                ps_q = await db.execute(
                    select(PositionStreak).filter_by(
                        user_email=email,
                        league_id=league_id
                    )
                )
                pos = {p.position: p for p in ps_q.scalars().all()}
                qb_streak = pos.get("QB").current_streak if pos.get("QB") else 0
                rb_streak = pos.get("RB").current_streak if pos.get("RB") else 0
                wr_streak = pos.get("WR").current_streak if pos.get("WR") else 0

                all_q = await db.execute(
                    select(AllPositionStreak).filter_by(
                        user_email=email,
                        league_id=league_id
                    )
                )
                all_obj = all_q.scalars().first()
                all_streak = all_obj.current_streak if all_obj else 0

            # ---- SIMULATE FUTURE PERFECT WEEKS ----
            projected_additional_points = 0
            projected_positions_total = {"qb": 0, "rb": 0, "wr": 0}

            cur_qb = qb_streak
            cur_rb = rb_streak
            cur_wr = wr_streak
            cur_all = all_streak

            for w in weeks_to_project:

                # Positional streak scoring: (1 + current streak)
                qb_pts = 1 + cur_qb
                rb_pts = 1 + cur_rb
                wr_pts = 1 + cur_wr

                projected_positions_total["qb"] += qb_pts
                projected_positions_total["rb"] += rb_pts
                projected_positions_total["wr"] += wr_pts

                projected_additional_points += qb_pts + rb_pts + wr_pts

                cur_qb += 1
                cur_rb += 1
                cur_wr += 1

                # Triple hit bonus: 5 * streak level
                cur_all += 1
                all_bonus = 5 * cur_all
                projected_additional_points += all_bonus

            projected_final_total = current_total_points + projected_additional_points

            results.append({
                "user_email": email,
                "current_total_points": current_total_points,
                "projected_additional_points": projected_additional_points,
                "projected_final_total": projected_final_total,
                "projected_positions_total": projected_positions_total,
                "final_projected_streaks": {
                    "qb_streak": cur_qb,
                    "rb_streak": cur_rb,
                    "wr_streak": cur_wr,
                    "all_positions_streak": cur_all
                },
                "weeks_projected": len(weeks_to_project)
            })

        results.sort(key=lambda r: r["projected_final_total"], reverse=True)

        return {
            "league_id": league_id,
            "season": season,
            "currentFinalizedWeek": currentFinalizedWeek,
            "projected_to_week": projected_end_week,
            "members": results
        }
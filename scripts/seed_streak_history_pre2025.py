"""
Seed 2019-2024 streak history for league 1 ("the OGs") from the spreadsheet
years, before the site existed.

These seasons have no picks or weekly_scores to generate from, so the rows are
hand-entered. Names are stored in the *_label columns rather than as user ids
because the real results do not fit a single user: ties, shared records, and
players who never had an account here.

Safe to re-run: skips any (league, season, scope) row that already exists.
Requires the fly proxy:  fly proxy 5433 -a fantasy-nfl-db
"""

import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.database import AsyncSession, async_engine
from app.models import StreakSeasonHistory

LEAGUE_ID = 1

# Transcribed verbatim from the league spreadsheet. Numbers are the record
# values; labels are who held them.
SEASONS = [
    dict(
        season=2019,
        champion_label="Patrick O'Neill",
        runner_up_label="Tom 6A",
        third_place_label="Nick Tomoff",
        member_count=16,
        best_triple_start=3, best_triple_start_label="Nick Tomoff",
        longest_triple_streak=3, longest_triple_label="Nick Tomoff",
        longest_qb_streak=11, longest_qb_label="Patrick O'Neill",
        longest_rb_streak=10, longest_rb_label="Corey Gracey",
        longest_wr_streak=6, longest_wr_label="Shaun Street",
        clinched_week=16, clinched_note="week 16",
        winner_score=160,
        most_triples_in_season=5,
        most_triples_label="Nick Tomoff & Patrick O'Neill & Cody Nevers",
    ),
    dict(
        season=2020,
        champion_label="Patrick O'Neill",
        runner_up_label="Tom 6A",
        third_place_label="Jason Cance",
        member_count=11,
        best_triple_start=1, best_triple_start_label="5 players",
        longest_triple_streak=5, longest_triple_label="Tom 6A",
        longest_qb_streak=15, longest_qb_label="Jason Cance",
        longest_rb_streak=7, longest_rb_label="Patrick O'Neill",
        longest_wr_streak=9, longest_wr_label="Jen Tomoff/Street",
        clinched_week=15, clinched_note="week 15",
        winner_score=248,
        most_triples_in_season=9, most_triples_label="Patrick O'Neill",
    ),
    dict(
        season=2021,
        champion_label="Tom 6A",
        runner_up_label="Dan Worek",
        third_place_label="Patrick O'Neill",
        member_count=9,
        best_triple_start=0, best_triple_start_label="no triples week 1",
        longest_triple_streak=3, longest_triple_label="Tom 6A & Kirsten Gentry",
        longest_qb_streak=10, longest_qb_label="Tom 6A",
        longest_rb_streak=8, longest_rb_label="Dan Worek",
        longest_wr_streak=5, longest_wr_label="Jason Cance & Patrick O'Neill",
        clinched_week=None, clinched_note="full season",
        winner_score=174,
        most_triples_in_season=6, most_triples_label="Tom 6A & Dan Worek",
    ),
    dict(
        season=2022,
        champion_label="Nick Tomoff",
        runner_up_label="Tom 6A",
        third_place_label="Patrick O'Neill",
        member_count=10,
        best_triple_start=2, best_triple_start_label="Patrick O'Neill",
        longest_triple_streak=3,
        longest_triple_label="Nick Tomoff (twice) & Dan Worek",
        longest_qb_streak=9, longest_qb_label="Nick Tomoff",
        longest_rb_streak=10, longest_rb_label="Tom 6A",
        longest_wr_streak=7, longest_wr_label="Nick Tomoff",
        clinched_week=None, clinched_note="final week controversy",
        winner_score=177,
        most_triples_in_season=7,
        most_triples_label="Nick Tomoff & Tom 6A & Patrick O'Neill",
    ),
    dict(
        season=2023,
        champion_label="Cody Nevers",
        runner_up_label="Kevin Watson",
        third_place_label="Jason Cance",
        member_count=12,
        best_triple_start=5, best_triple_start_label="Cody Nevers",
        longest_triple_streak=5, longest_triple_label="Cody Nevers",
        longest_qb_streak=12, longest_qb_label="Kevin Watson",
        longest_rb_streak=15, longest_rb_label="Jason Cance",
        longest_wr_streak=6, longest_wr_label="Jen Street & Kevin Watson",
        clinched_week=None, clinched_note="final week close match",
        winner_score=236,
        most_triples_in_season=9, most_triples_label="Cody Nevers",
    ),
    dict(
        season=2024,
        champion_label="Tom 6A / Patrick O'Neill",   # tie
        runner_up_label=None,                        # blank in the spreadsheet
        third_place_label="Jason Cance",
        member_count=9,
        best_triple_start=2, best_triple_start_label="Nick Tomoff",
        longest_triple_streak=4, longest_triple_label="Patrick O'Neill",
        longest_qb_streak=14, longest_qb_label="Tom 6A",
        longest_rb_streak=7, longest_rb_label="Patrick O'Neill",
        longest_wr_streak=7, longest_wr_label="Nick Tomoff & Jason Cance",
        clinched_week=None, clinched_note="final week close match",
        winner_score=159,
        most_triples_in_season=7, most_triples_label="Patrick O'Neill",
    ),
]


async def main():
    async with AsyncSession(async_engine) as session:
        added, skipped = [], []

        for data in SEASONS:
            existing = await session.execute(
                select(StreakSeasonHistory).where(
                    StreakSeasonHistory.league_id == LEAGUE_ID,
                    StreakSeasonHistory.season == data["season"],
                    StreakSeasonHistory.scope == "league",
                )
            )
            if existing.scalar_one_or_none():
                skipped.append(data["season"])
                continue

            session.add(
                StreakSeasonHistory(scope="league", league_id=LEAGUE_ID, **data)
            )
            added.append(data["season"])

        await session.commit()

        print(f"added:   {added or 'none'}")
        print(f"skipped: {skipped or 'none'} (already present)")

        rows = await session.execute(
            select(StreakSeasonHistory)
            .where(StreakSeasonHistory.league_id == LEAGUE_ID)
            .order_by(StreakSeasonHistory.season)
        )
        print("\nleague 1 history now covers:")
        for r in rows.scalars().all():
            print(
                f"  {r.season}  champ={r.champion_label or r.champion_id}"
                f"  members={r.member_count}  longest_triple={r.longest_triple_streak}"
            )


if __name__ == "__main__":
    asyncio.run(main())

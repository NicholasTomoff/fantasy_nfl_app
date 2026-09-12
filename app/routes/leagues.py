from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Optional
from datetime import timezone, datetime

from app import models, schemas
from app.database import get_db
from app.auth import get_current_user  # Auth dependency we built
from app.utils.membership import (mark_in_for_season, check_in_is_open,
                                  check_in_deadline)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/api/leagues",
    tags=["leagues"],
)

def ensure_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Return a naive UTC datetime (no tzinfo). If dt is None -> None.
    If dt is timezone-aware -> convert to UTC and strip tzinfo.
    If dt is naive -> assume it's already UTC and return as-is.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt  # assume naive UTC already
    # convert to UTC then strip tzinfo
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

# --------- Create New League ---------
@router.post("", response_model=schemas.League)
async def create_league(league_in: schemas.LeagueCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user), ):
    # Check if league name already exists
    result = await db.execute(select(models.League).where(models.League.name == league_in.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League with this name already exists.",
        )

    league = models.League(
        name=league_in.name,
        min_players=league_in.min_players,
        season_year=league_in.season_year,
        created_by_user_id=current_user.id,
    )
    db.add(league)
    await db.commit()
    await db.refresh(league)
    return league

# --------- Get Info about Leagues for the Logged in User ---------
@router.get("", response_model=List[schemas.League])
async def get_leagues(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user),):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    stmt = (
        select(models.League)
        .where(models.League.members.any(models.LeagueMember.user_id == current_user.id))
        .options(
            selectinload(models.League.members).selectinload(models.LeagueMember.user),
            selectinload(models.League.host)
        )
    )

    result = await db.execute(stmt)
    leagues = result.scalars().unique().all()

    return leagues

# --------- Get Info about All Leagues ---------
@router.get("/all", response_model=List[schemas.League])
async def get_all_leagues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.League).options(
            joinedload(models.League.members).joinedload(models.LeagueMember.user),
            joinedload(models.League.host)  # Optional: load host info
        )
    )
    leagues = result.scalars().unique().all()
    return leagues

# --------- Get Info about All Members of a League ---------
@router.get("/{league_id}/members", response_model=List[schemas.UserSummary])
async def get_league_members(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.League)
        .where(models.League.id == league_id)
        .options(
            joinedload(models.League.members).joinedload(models.LeagueMember.user)
        )
    )
    league =  result.scalars().unique().one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    users = [member.user for member in league.members]
    return users

# --------- Insert User into League ---------
@router.post("/{league_id}/join", response_model=schemas.LeagueMemberResponse)
async def join_league(league_id: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user),):
    result = await db.execute(
        select(models.League).where(models.League.id == league_id)
    )
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    result = await db.execute(
        select(models.LeagueMember).where(
            models.LeagueMember.league_id == league_id,
            models.LeagueMember.user_id == current_user.id,
        )
    )
    existing_member = result.scalar_one_or_none()
    if existing_member:
        raise HTTPException(status_code=400, detail="User already joined this league")

    new_member = models.LeagueMember(league_id=league_id, user_id=current_user.id)
    db.add(new_member)
    # Joining is an answer -- see mark_in_for_season.
    await mark_in_for_season(db, league_id, league.season_year, current_user.id)
    await db.commit()
    await db.refresh(new_member)

    return {"league_id": league_id, "user_id": current_user.id, "joined": True}

# --------- Get Info about League from league_id ---------
@router.get("/{league_id}", response_model=schemas.League)
async def get_league_by_id(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.League)
        .where(models.League.id == league_id)
        .options(
            joinedload(models.League.members).joinedload(models.LeagueMember.user)
        )
    )
    league = result.scalars().unique().one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    return league

# ---------------- Get league finance info ----------------
@router.get("/{league_id}/season/{season_year}/finance",
            response_model=schemas.LeagueSeasonFinanceOut)
async def get_league_finance(league_id: int, season_year: int, db: AsyncSession = Depends(get_db),):
    try:
        logger.info(f"🔍 GET FINANCE: league={league_id}, season_year={season_year}")

        # ---------------- LOAD SEASON ----------------
        logger.info("➡️ Querying Season row...")
        season_result = await db.execute(
            select(models.Season).filter_by(year=season_year)
        )
        season = season_result.scalars().unique().one_or_none()
        logger.info(f"Season result: {season}")

        if not season:
            logger.info("⚠️ No season found, returning empty finance response.")
            return schemas.LeagueSeasonFinanceOut(
                id=0,
                league_id=league_id,
                season_year=season_year,
                entry_fee=None,
                total_pot=0,
                payouts={},
                member_payments=[]
            )

        # ---------------- LOAD LEAGUE + MEMBERS (use same pattern as get_league_members) ----------------
        logger.info("➡️ Querying League + members (with user) ...")
        league_result = await db.execute(
            select(models.League)
            .where(models.League.id == league_id)
            .options(
                joinedload(models.League.members).joinedload(models.LeagueMember.user)
            )
        )
        league = league_result.scalars().unique().one_or_none()
        logger.info(f"League result: {league}")

        if not league:
            logger.info("⚠️ League not found, returning empty finance response.")
            return schemas.LeagueSeasonFinanceOut(
                id=0,
                league_id=league_id,
                season_year=season_year,
                entry_fee=None,
                total_pot=0,
                payouts={},
                member_payments=[]
            )

        # ---------------- LOAD FINANCE ----------------
        logger.info("➡️ Querying LeagueSeasonFinance row...")
        finance_result = await db.execute(
            select(models.LeagueSeasonFinance)
            .options(
                joinedload(models.LeagueSeasonFinance.member_payments)
                .joinedload(models.LeagueSeasonMemberPayment.user)
            )
            .filter_by(league_id=league_id, season_id=season.id)
        )
        finance = finance_result.scalars().unique().one_or_none()
        logger.info(f"Finance result: {finance}")

        # If finance exists -> use it (and return actual member_payments from DB)
        if finance:
            # Recalculate total pot if needed
            if finance.entry_fee is not None:
                member_count = len(league.members)  # use actual members, not member_payments
                finance.total_pot = finance.entry_fee * member_count

            # Build member payments list: use existing payments, but fill in missing users
            member_payments_out = []
            league_member_map = {m.user.id: m.user for m in league.members if m.user}
            finance_user_ids = {mp.user_id for mp in finance.member_payments}

            # Existing payments
            for mp in finance.member_payments:
                member_payments_out.append(
                    schemas.LeagueSeasonMemberPaymentOut(
                        id=mp.id,
                        season_finance_id=mp.season_finance_id,
                        user_id=mp.user_id,
                        user_name=mp.user.name if mp.user else league_member_map.get(mp.user_id).name if mp.user_id in league_member_map else None,
                        paid=mp.paid,
                        paid_date=mp.paid_date
                    )
                )

            # Add placeholders for league members without payments
            for user_id, user in league_member_map.items():
                if user_id not in finance_user_ids:
                    member_payments_out.append(
                        schemas.LeagueSeasonMemberPaymentOut(
                            id=0,
                            season_finance_id=finance.id,
                            user_id=user.id,
                            user_name=user.name,
                            paid=False,
                            paid_date=None
                        )
                    )

            return schemas.LeagueSeasonFinanceOut(
                id=finance.id,
                league_id=finance.league_id,
                season_year=season.year,
                entry_fee=finance.entry_fee,
                total_pot=finance.total_pot,
                payouts=finance.payouts or {},
                member_payments=member_payments_out
            )

        # No finance row for this league/season yet -- normal for a season nobody
        # has set an entry fee for. Previously the function just fell off the end
        # and returned None, which failed response_model validation as a 500 and
        # made the whole admin page unloadable.
        logger.info("No finance row yet; returning an empty sheet with the roster.")
        return schemas.LeagueSeasonFinanceOut(
            id=0,
            league_id=league_id,
            season_year=season_year,
            entry_fee=None,
            total_pot=0,
            payouts={},
            member_payments=[
                schemas.LeagueSeasonMemberPaymentOut(
                    id=0,
                    season_finance_id=0,
                    user_id=m.user.id,
                    user_name=m.user.name or m.user.email,
                    paid=False,
                    paid_date=None,
                )
                for m in league.members if m.user
            ],
        )

    except SQLAlchemyError:
        logger.exception("❌ SQLAlchemy database error occurred!")
        raise HTTPException(status_code=500, detail="Database query failed")

    except Exception as e:
        logger.exception("❌ Unexpected server error occurred!")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Post update entry fee ----------------
@router.post("/{league_id}/season/{season_year}/finance/entry_fee", response_model=schemas.LeagueSeasonFinanceOut)
async def update_entry_fee(league_id: int, season_year: int, payload: schemas.LeagueSeasonFinanceEntryFeeUpdate, db: AsyncSession = Depends(get_db),):
    # ---------------- LOAD SEASON ----------------
    season_result = await db.execute(select(models.Season).filter_by(year=season_year))
    season = season_result.scalars().unique().one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # ---------------- LOAD LEAGUE WITH MEMBERS ----------------
    league_result = await db.execute(
        select(models.League)
        .where(models.League.id == league_id)
        .options(joinedload(models.League.members).joinedload(models.LeagueMember.user))
    )
    league = league_result.scalars().unique().one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get member count and log
    members = league.members
    member_count = len(members)
    logger.info(f"League has {league_id} - {member_count} members")

    # ---------------- LOAD OR CREATE FINANCE ----------------
    finance_result = await db.execute(
        select(models.LeagueSeasonFinance)
        .filter_by(league_id=league_id, season_id=season.id)
        .options(joinedload(models.LeagueSeasonFinance.member_payments).joinedload(models.LeagueSeasonMemberPayment.user))
    )
    finance = finance_result.scalars().unique().one_or_none()

    if not finance:
        logger.info("No finance row exists, creating new")
        finance = models.LeagueSeasonFinance(
            league_id=league_id,
            season_id=season.id,
            entry_fee=float(payload.entry_fee),
            total_pot=float(payload.entry_fee) * member_count,
            payouts={}
        )
        db.add(finance)
    else:
        logger.info(f"Finance exists (id={finance.id}), updating entry fee and total pot")
        finance.entry_fee = float(payload.entry_fee)
        finance.total_pot = finance.entry_fee * member_count

    await db.commit()
    await db.refresh(finance)
    logger.info(f"Finance updated: entry_fee={finance.entry_fee}, total_pot={finance.total_pot}")

    # ---------------- BUILD MEMBER PAYMENTS ----------------
    member_payments_out = []
    for mp in finance.member_payments:
        member_payments_out.append(
            schemas.LeagueSeasonMemberPaymentOut(
                id=mp.id,
                season_finance_id=mp.season_finance_id,
                user_id=mp.user_id,
                user_name=mp.user.name if mp.user else None,
                paid=mp.paid,
                paid_date=mp.paid_date
            )
        )

    # ---------------- RETURN ----------------
    return schemas.LeagueSeasonFinanceOut(
        id=finance.id,
        league_id=finance.league_id,
        season_year=season.year,
        entry_fee=finance.entry_fee,
        total_pot=finance.total_pot,
        payouts=finance.payouts or {},
        member_payments=member_payments_out
    )

# ---------------- Post league payout info ----------------
@router.post("/{league_id}/season/{season_year}/finance/payouts", response_model=schemas.LeagueSeasonFinanceOut)
async def update_payouts(league_id: int, season_year: int, payload: schemas.LeagueSeasonFinancePayoutUpdate, db: AsyncSession = Depends(get_db),):
    # Get Season
    season_result = await db.execute(select(models.Season).filter_by(year=season_year))
    season = season_result.scalars().unique().one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Get Finance row
    finance_result = await db.execute(
        select(models.LeagueSeasonFinance)
        .options(joinedload(models.LeagueSeasonFinance.member_payments).joinedload(models.LeagueSeasonMemberPayment.user))
        .filter_by(league_id=league_id, season_id=season.id)
    )
    finance = finance_result.scalars().unique().one_or_none()
    if not finance:
        raise HTTPException(status_code=404, detail="Finance record not found")

    # Update payouts
    finance.payouts = payload.payouts
    await db.commit()
    await db.refresh(finance)

    # Convert to Pydantic
    return schemas.LeagueSeasonFinanceOut(
        id=finance.id,
        league_id=finance.league_id,
        season_year=season.year,
        entry_fee=finance.entry_fee,
        total_pot=finance.total_pot,
        payouts=finance.payouts or {},
        member_payments=[
            schemas.LeagueSeasonMemberPaymentOut(
                id=mp.id,
                season_finance_id=mp.season_finance_id,  # <-- REQUIRED FIELD
                user_id=mp.user_id,
                user_name=mp.user.name if mp.user else None,
                paid=mp.paid,
                paid_date=mp.paid_date
            )
            for mp in finance.member_payments
        ]
    )

# ---------------- Post user payment for league entry fee ----------------
@router.post("/{league_id}/season/{season_year}/member/{user_id}/payment",
             response_model=schemas.LeagueSeasonFinanceOut)
async def toggle_member_payment(league_id: int, season_year: int, user_id: int, payload: schemas.LeagueSeasonMemberPaymentUpdate, db: AsyncSession = Depends(get_db),):
    # Get Season
    season_result = await db.execute(select(models.Season).filter_by(year=season_year))
    season = season_result.scalars().unique().one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Get Finance row
    finance_result = await db.execute(
        select(models.LeagueSeasonFinance)
        .options(
            joinedload(models.LeagueSeasonFinance.member_payments)
            .joinedload(models.LeagueSeasonMemberPayment.user)
        )
        .filter_by(league_id=league_id, season_id=season.id)
    )
    finance = finance_result.scalars().unique().one_or_none()
    if not finance:
        raise HTTPException(status_code=404, detail="Finance record not found")

    # Find existing member payment if it exists
    member_payment = next((m for m in finance.member_payments
                           if m.user_id == user_id), None)

    # If no existing member payment → create it
    if not member_payment:
        member_payment = models.LeagueSeasonMemberPayment(
            season_finance_id=finance.id,
            user_id=user_id,
            paid=False,
            paid_date=None
        )
        db.add(member_payment)
        await db.flush()       # get IDs populated
        await db.refresh(member_payment)
        finance.member_payments.append(member_payment)

    # --- Update payment status ---
    member_payment.paid = payload.paid

    if payload.paid:
        member_payment.paid_date = ensure_naive_utc(payload.paid_date) or datetime.utcnow()
    else:
        member_payment.paid_date = None

    # Total pot update (optional — entry fee logic handled elsewhere)
    # if finance.entry_fee is not None:
    #     finance.total_pot = finance.entry_fee * len(finance.member_payments)

    await db.commit()
    await db.refresh(finance)

    # --- Return proper schema (FIXED missing season_finance_id) ---
    return schemas.LeagueSeasonFinanceOut(
        id=finance.id,
        league_id=finance.league_id,
        season_year=season.year,
        entry_fee=finance.entry_fee,
        total_pot=finance.total_pot,
        payouts=finance.payouts or {},
        member_payments=[
            schemas.LeagueSeasonMemberPaymentOut(
                id=mp.id,
                season_finance_id=mp.season_finance_id,  # <-- REQUIRED FIELD
                user_id=mp.user_id,
                user_name=mp.user.name if mp.user else None,
                paid=mp.paid,
                paid_date=mp.paid_date
            )
            for mp in finance.member_payments
        ]
    )


# =====================================================================
# Season check-in: who is playing this league this season
#
# league_members is the permanent roster and is never deleted, so a member
# who sits out keeps every pick, score and podium finish from prior seasons.
# league_season_members answers "are you in for THIS year".
# =====================================================================

async def _load_league(league_id: int, db: AsyncSession) -> models.League:
    result = await db.execute(
        select(models.League)
        .where(models.League.id == league_id)
        .options(joinedload(models.League.members).joinedload(models.LeagueMember.user))
    )
    league = result.scalars().unique().one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league


async def _season_member_rows(league_id: int, season_year: int, db: AsyncSession):
    result = await db.execute(
        select(models.LeagueSeasonMember).filter_by(
            league_id=league_id, season_year=season_year
        )
    )
    return {r.user_id: r for r in result.scalars().all()}


def _roster_response(league, season_year, rows, current_user, check_in_open=True, closes_at=None) -> schemas.LeagueSeasonRosterOut:
    is_commissioner = league.created_by_user_id == current_user.id
    members, counts = [], {"in": 0, "out": 0, "pending": 0}
    my_status = schemas.SeasonMemberStatus.pending

    for m in league.members:
        if not m.user:
            continue
        row = rows.get(m.user.id)
        status = row.status if row else "pending"
        counts[status] = counts.get(status, 0) + 1
        if m.user.id == current_user.id:
            my_status = schemas.SeasonMemberStatus(status)
        members.append(
            schemas.LeagueSeasonMemberOut(
                user_id=m.user.id,
                user_name=m.user.name,
                user_email=m.user.email,
                status=schemas.SeasonMemberStatus(status),
                responded_at=row.responded_at if row else None,
                set_by_commissioner=bool(row and row.set_by_user_id),
            )
        )

    members.sort(key=lambda x: (x.status != "in", (x.user_name or "").lower()))
    return schemas.LeagueSeasonRosterOut(
        league_id=league.id,
        league_name=league.name,
        season_year=season_year,
        is_commissioner=is_commissioner,
        check_in_open=check_in_open,
        check_in_closes_at=closes_at,
        my_status=my_status,
        counts=counts,
        members=members,
    )


async def _set_status(league_id, season_year, user_id, status, db, set_by=None):
    """Upsert one member's season status. Caller has already authorised."""
    result = await db.execute(
        select(models.LeagueSeasonMember).filter_by(
            league_id=league_id, season_year=season_year, user_id=user_id
        )
    )
    row = result.scalars().one_or_none()
    if row:
        row.status = status
        row.responded_at = datetime.utcnow()
        row.set_by_user_id = set_by
    else:
        db.add(
            models.LeagueSeasonMember(
                league_id=league_id,
                season_year=season_year,
                user_id=user_id,
                status=status,
                responded_at=datetime.utcnow(),
                set_by_user_id=set_by,
            )
        )
    await db.commit()


# --------- Season roster with member's status ---------
@router.get("/{league_id}/season/{season_year}/roster", response_model=schemas.LeagueSeasonRosterOut)
async def get_season_roster(league_id: int, season_year: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    league = await _load_league(league_id, db)
    rows = await _season_member_rows(league_id, season_year, db)
    return _roster_response(league, season_year, rows, current_user,
                            await check_in_is_open(db, season_year),
                            await check_in_deadline(db, season_year))


# --------- Open the season: create pending rows for the whole roster ---------
@router.post("/{league_id}/season/{season_year}/open", response_model=schemas.LeagueSeasonRosterOut)
async def open_season(league_id: int, season_year: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    league = await _load_league(league_id, db)
    if league.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the league commissioner can open a season.")

    season = (await db.execute(select(models.Season).filter_by(year=season_year))).scalars().first()
    if not season:
        raise HTTPException(status_code=400, detail=f"No season row for {season_year}.")

    existing = await _season_member_rows(league_id, season_year, db)
    created = 0
    for m in league.members:
        if m.user and m.user.id not in existing:
            db.add(
                models.LeagueSeasonMember(
                    league_id=league_id,
                    season_year=season_year,
                    user_id=m.user.id,
                    status="pending",
                )
            )
            created += 1
    if created:
        await db.commit()
    logger.info(f"Opened season {season_year} for league {league_id}: {created} pending rows")

    rows = await _season_member_rows(league_id, season_year, db)
    return _roster_response(league, season_year, rows, current_user,
                            await check_in_is_open(db, season_year),
                            await check_in_deadline(db, season_year))


# --------- Member answers "in" or "out" for themselves ---------
@router.post("/{league_id}/season/{season_year}/me", response_model=schemas.LeagueSeasonRosterOut)
async def set_my_season_status(league_id: int, season_year: int, payload: schemas.SeasonMemberStatusUpdate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    league = await _load_league(league_id, db)
    if not any(m.user_id == current_user.id for m in league.members):
        raise HTTPException(status_code=403, detail="You are not a member of this league.")

    await _set_status(league_id, season_year, current_user.id, payload.status.value, db)
    rows = await _season_member_rows(league_id, season_year, db)
    return _roster_response(league, season_year, rows, current_user,
                            await check_in_is_open(db, season_year),
                            await check_in_deadline(db, season_year))


# --------- Commissioner sets a member's status ---------
@router.post("/{league_id}/season/{season_year}/member/{user_id}/status", response_model=schemas.LeagueSeasonRosterOut)
async def set_member_season_status(league_id: int, season_year: int, user_id: int, payload: schemas.SeasonMemberStatusUpdate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    league = await _load_league(league_id, db)
    if league.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the league commissioner can set another member's status.")
    if not any(m.user_id == user_id for m in league.members):
        raise HTTPException(status_code=404, detail="That user is not on this league's roster.")

    await _set_status(league_id, season_year, user_id, payload.status.value, db, set_by=current_user.id)
    rows = await _season_member_rows(league_id, season_year, db)
    return _roster_response(league, season_year, rows, current_user,
                            await check_in_is_open(db, season_year),
                            await check_in_deadline(db, season_year))

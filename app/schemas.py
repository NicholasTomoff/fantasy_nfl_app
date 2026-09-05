from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# ------------- Team Schema -------------
class TeamOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# ------------- Player Schema -------------
class PlayerOut(BaseModel):
    player_id: int
    player_name: str
    position: str
    team: Optional[TeamOut] = None  # <-- allow nullable team

    class Config:
        orm_mode = True

class UserSummary(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        orm_mode = True
        
# ------------- Weekly Player Pick -------------
class PickCreate(BaseModel):
    user_email: str
    league_id: int
    season: int
    week: int
    qb: str
    rb: str
    wr: str
    timestamp: Optional[datetime] = None  # Optional; will default to now if missing

    class Config:
        orm_mode = True

class PickCreate(PickCreate):
    pass

class PickOut(PickCreate):
    id: int
    user: Optional[UserSummary]  # <-- nested user info here

    class Config:
        orm_mode = True

# ------------- User Schema -------------
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class LeagueOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class UserOut(UserBase):
    id: int
    leagues: List[LeagueOut] = Field(default_factory=list)

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    user: UserOut
    token: str

# ------------- NFL Games -------------
class NFLGameOut(BaseModel):
    id: int
    status: Optional[str] = None  # instead of str
    season: int
    stage: str
    week: str
    date: datetime

    home_team: str
    home_team_id: int
    away_team: str
    away_team_id: int

    home_score: int | None = None
    away_score: int | None = None

    class Config:
        orm_mode = True

class PlayerGameStatBase(BaseModel):
    player_id: int
    team_id: int
    game_id: int
    position: str | None = None

    passing_yards: int | None = None
    passing_tds: int | None = None
    rushing_yards: int | None = None
    rushing_tds: int | None = None
    receiving_yards: int | None = None
    receiving_tds: int | None = None
    receptions: int | None = None

class PlayerGameStatCreate(PlayerGameStatBase):
    pass

class PlayerGameStatOut(PlayerGameStatBase):
    id: int
    created_at: datetime
    player: Optional[PlayerOut] = None  # ✅ Add this field
    game: Optional[NFLGameOut] = None  # ✅ Include game info (season, week, etc.)


    class Config:
        orm_mode = True

# Weekly scoring models
class WeeklyScoreBase(BaseModel):
    user_email: Optional[str] = ""
    week: int
    season: int
    league_id: int  # ✅ new field

    qb_points: Optional[int] = 0
    rb_points: Optional[int] = 0
    wr_points: Optional[int] = 0

    qb_streak: Optional[int] = 0
    rb_streak: Optional[int] = 0
    wr_streak: Optional[int] = 0

    all_positions_hit: Optional[bool] = False
    all_positions_bonus: Optional[int] = 0

    total_points: Optional[int] = 0

    class Config:
        orm_mode = True

class WeeklyScoreCreate(WeeklyScoreBase):
    pass

class WeeklyScoreRead(WeeklyScoreBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class PositionStreakBase(BaseModel):
    user_email: str
    position: str  # "QB", "RB", "WR"
    current_streak: int
    league_id: int  # ✅ new field

class PositionStreakCreate(PositionStreakBase):
    pass

class PositionStreakRead(PositionStreakBase):
    id: int

    class Config:
        orm_mode = True

class AllPositionStreakBase(BaseModel):
    user_email: str
    current_streak: int
    league_id: int  # ✅ new field

class AllPositionStreakCreate(AllPositionStreakBase):
    pass

class AllPositionStreakRead(AllPositionStreakBase):
    id: int

    class Config:
        orm_mode = True

class TopPlayerOut(BaseModel):
    player: PlayerOut
    total_yards: int

# ------------- Leagues Schema -------------
class LeagueBase(BaseModel):
    name: constr(min_length=3, max_length=50)
    min_players: Optional[int] = 4
    season_year: int

class LeagueCreate(LeagueBase):
    pass

class LeagueInDBBase(LeagueBase):
    id: int
    created_by_user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class LeagueMemberResponse(BaseModel):
    league_id: int
    user_id: int
    joined: bool

    class Config:
        orm_mode = True

class LeagueMemberUser(BaseModel):
    id: int
    user: UserSummary

    class Config:
        orm_mode = True

class League(LeagueInDBBase):
    members: List[LeagueMemberUser] = []

    class Config:
        orm_mode = True

# --- Member Payment ---
class LeagueSeasonMemberPaymentBase(BaseModel):
    user_id: int
    paid: bool = False
    paid_date: Optional[datetime] = None

class LeagueSeasonMemberPaymentCreate(LeagueSeasonMemberPaymentBase):
    season_finance_id: int

class LeagueSeasonMemberPaymentOut(LeagueSeasonMemberPaymentBase):
    id: int
    season_finance_id: int
    user_name: Optional[str] = None  # optional join

    class Config:
        orm_mode = True

# --- League Season Finance ---
class LeagueSeasonFinanceBase(BaseModel):
    entry_fee: Optional[float] = None
    total_pot: Optional[float] = 0
    payouts: Dict[str, float] = Field(default_factory=dict)

class LeagueSeasonFinanceCreate(LeagueSeasonFinanceBase):
    league_id: int
    season_year: int

class LeagueSeasonFinanceOut(LeagueSeasonFinanceBase):
    id: int
    league_id: int
    season_year: int
    member_payments: List[LeagueSeasonMemberPaymentOut] = Field(default_factory=list)

    class Config:
        orm_mode = True

class LeagueSeasonFinanceEntryFeeUpdate(BaseModel):
    entry_fee: float

class LeagueSeasonFinancePayoutUpdate(BaseModel):
    payouts: Dict[str, float]

class LeagueSeasonMemberPaymentUpdate(BaseModel):
    paid: bool
    paid_date: Optional[datetime] = None

# --- League Season Membership (per-season "are you in?" check-in) ---
class SeasonMemberStatus(str, Enum):
    pending = "pending"
    in_ = "in"
    out = "out"


class LeagueSeasonMemberOut(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    status: SeasonMemberStatus = SeasonMemberStatus.pending
    responded_at: Optional[datetime] = None
    set_by_commissioner: bool = False

    class Config:
        orm_mode = True


class LeagueSeasonRosterOut(BaseModel):
    league_id: int
    league_name: Optional[str] = None
    season_year: int
    is_commissioner: bool = False
    my_status: SeasonMemberStatus = SeasonMemberStatus.pending
    counts: Dict[str, int] = Field(default_factory=dict)
    members: List[LeagueSeasonMemberOut] = Field(default_factory=list)


class SeasonMemberStatusUpdate(BaseModel):
    status: SeasonMemberStatus


# --- Streak History ---
class StreakHistoryBase(BaseModel):
    # Every column on streak_season_history is nullable, and the generator does
    # not populate podium finishes at all; the global row also omits the per-user
    # ids. Requiring them here makes the endpoint 500 on real rows.
    scope: str
    league_id: Optional[int] = None
    season: int

    champion_id: Optional[int] = None
    runner_up_id: Optional[int] = None
    third_place_id: Optional[int] = None

    member_count: Optional[int] = None

    best_triple_start: Optional[int] = None
    best_triple_start_user_id: Optional[int] = None

    longest_triple_streak: Optional[int] = None
    longest_triple_user_id: Optional[int] = None

    longest_qb_streak: Optional[int] = None
    longest_rb_streak: Optional[int] = None
    longest_wr_streak: Optional[int] = None

    most_triples_in_season: Optional[int] = None
    most_triples_user_id: Optional[int] = None

    clinched_week: Optional[int] = None


class StreakHistoryCreate(StreakHistoryBase):
    pass


class StreakHistoryOut(StreakHistoryBase):
    id: int

    # Resolved from the *_id columns by the route -- the page shows names.
    champion_name: Optional[str] = None
    runner_up_name: Optional[str] = None
    third_place_name: Optional[str] = None

    class Config:
        from_attributes = True    
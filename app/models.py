from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean, Date, ForeignKeyConstraint, UniqueConstraint, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from sqlalchemy.sql import func

# ------------- Seasons           -------------
class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    year = Column(Integer, unique=True, nullable=False)
    is_current = Column(Boolean, default=False)
    start_date = Column(Date)
    end_date = Column(Date)

# ------------- Teams and Players -------------
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, index=True)
    player_name = Column(String)
    position = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team_name = Column(String)
    active = Column(Boolean, default=True)                              # added Aug 20, 2025

    team = relationship("Team", back_populates="players", lazy="joined")

    __table_args__ = (
        UniqueConstraint("player_id", "team_id", name="uq_player_team"),
    )

# ------------- Weekly Picks -------------
class WeeklyPick(Base):
    __tablename__ = "picks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week = Column(Integer, index=True)
    user_email = Column(String, ForeignKey("users.email"))  # <-- this FK is essential
    season = Column(Integer)
    league_id = Column(Integer, ForeignKey("leagues.id"))  # <-- 🆕 added July 15, 2025
    qb = Column(String)
    rb = Column(String)
    wr = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="picks", lazy="joined")
    league = relationship("League", back_populates="picks", lazy="raise")  # 🛡️ prevent async issues

# ------------- Users -------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)

    picks = relationship("WeeklyPick", back_populates="user", cascade="all, delete", lazy="selectin")
    hosted_leagues = relationship("League", back_populates="host", cascade="all, delete", lazy="selectin")
    memberships = relationship("LeagueMember", back_populates="user", cascade="all, delete", lazy="selectin")

    @property
    def leagues(self):
        return [m.league for m in self.memberships if m.league]
    
# ------------- NFL Games -------------
class NFLGame(Base):
    __tablename__ = "nfl_games"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    season = Column(Integer)
    week = Column(String)
    stage = Column(String, nullable=True)

    date = Column(DateTime)
    status = Column(String)

    home_team = Column(String)
    home_team_id = Column(Integer)
    away_team = Column(String)
    away_team_id = Column(Integer)

    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_nfl_games_season_week", "season", "week"),
    )

class PlayerGameStat(Base):
    __tablename__ = "player_game_stats"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    player_id = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=False)
    game_id = Column(Integer, ForeignKey("nfl_games.id"))
    position = Column(String, nullable=True)

    passing_yards = Column(Integer, nullable=True)
    passing_tds = Column(Integer, nullable=True)
    rushing_yards = Column(Integer, nullable=True)
    rushing_tds = Column(Integer, nullable=True)
    receiving_yards = Column(Integer, nullable=True)
    receiving_tds = Column(Integer, nullable=True)
    receptions = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ["player_id", "team_id"],
            ["players.player_id", "players.team_id"]
        ),
    )

    player = relationship(
        "Player",
        primaryjoin="and_(PlayerGameStat.player_id == Player.player_id, PlayerGameStat.team_id == Player.team_id)",
        backref="game_stats"
    )

    game = relationship("NFLGame")

# ------------- Weekly Scores & Streaks -------------
class WeeklyScore(Base):
    __tablename__ = "weekly_scores"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_email = Column(String, index=True)
    week = Column(Integer, index=True)
    season = Column(Integer, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))  # <-- 🆕 added July 15, 2025

    qb_points = Column(Integer, nullable=True)
    rb_points = Column(Integer, nullable=True)
    wr_points = Column(Integer, nullable=True)

    qb_streak = Column(Integer, default=0)
    rb_streak = Column(Integer, default=0)
    wr_streak = Column(Integer, default=0)

    all_positions_hit = Column(Boolean, nullable=True)
    all_positions_bonus = Column(Integer, nullable=True)

    total_points = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    
class PositionStreak(Base):
    __tablename__ = "position_streaks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String, index=True)
    position = Column(String)
    current_streak = Column(Integer, default=0)
    last_updated_week = Column(Integer, nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))  # <-- 🆕 added July 15, 2025

class AllPositionStreak(Base):
    __tablename__ = "all_position_streaks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String, index=True)
    current_streak = Column(Integer, default=0)
    last_updated_week = Column(Integer, nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))  # <-- 🆕 added July 15, 2025

# ------------- Leagues & Memberships -------------
class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    min_players = Column(Integer, default=4)
    season_year = Column(Integer, nullable=False)
    banner = Column(String, default="https://images.pexels.com/photos/7005488/pexels-photo-7005488.jpeg")

    host = relationship("User", back_populates="hosted_leagues", lazy="joined")  # good for async access
    members = relationship("LeagueMember", back_populates="league", cascade="all, delete", lazy="selectin")

    # Optional: for accessing weekly picks related to a league (added July 2025)
    picks = relationship("WeeklyPick", back_populates="league", cascade="all, delete", lazy="selectin")

class LeagueMember(Base):
    __tablename__ = "league_members"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    league = relationship("League", back_populates="members", lazy="joined")
    user = relationship("User", back_populates="memberships", lazy="joined")

    __table_args__ = (
        UniqueConstraint('user_id', 'league_id', name='uq_user_league'),
    )

class LeagueSeasonMember(Base):
    """
    Per-season participation for a league.

    `league_members` stays the permanent roster -- "has ever played here" -- and is
    never deleted, which is what keeps a departed member's picks, scores and podium
    finishes resolvable. This table answers the separate question of who is actually
    playing in a given season.
    """
    __tablename__ = "league_season_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    season_year = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="pending")  # pending | in | out
    responded_at = Column(DateTime, nullable=True)
    # set by a commissioner override rather than the member themselves
    set_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    league = relationship("League", backref="season_members", lazy="selectin")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("league_id", "season_year", "user_id", name="uq_league_season_member"),
    )

class LeagueInviteToken(Base):
    __tablename__ = "league_invite_tokens"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String, unique=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    league = relationship("League", backref="invite_tokens")

class LeagueSeasonFinance(Base):
    __tablename__ = "league_season_finances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)
    entry_fee = Column(Float, nullable=True)
    total_pot = Column(Float, default=0)
    payouts = Column(JSON, nullable=True)

    league = relationship("League", backref="season_finances", lazy="selectin")
    season = relationship("Season", lazy="selectin")
    member_payments = relationship(
        "LeagueSeasonMemberPayment",
        back_populates="season_finance",
        cascade="all, delete",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("league_id", "season_id", name="uq_league_season_finance"),
    )

class LeagueSeasonMemberPayment(Base):
    __tablename__ = "league_season_member_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    season_finance_id = Column(Integer, ForeignKey("league_season_finances.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    paid = Column(Boolean, default=False)
    paid_date = Column(DateTime, nullable=True)

    user = relationship("User", backref="season_payments", lazy="selectin")
    season_finance = relationship(
        "LeagueSeasonFinance",
        back_populates="member_payments",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint("season_finance_id", "user_id", name="uq_finance_user_payment"),
    )

class StreakSeasonHistory(Base):
    __tablename__ = "streak_season_history"

    id = Column(Integer, primary_key=True)
    scope = Column(String, default="league")
    league_id = Column(Integer, ForeignKey("leagues.id"), index=True, nullable=True)
    season = Column(Integer, index=True)

    champion_id = Column(Integer, ForeignKey("users.id"))
    runner_up_id = Column(Integer, ForeignKey("users.id"))
    third_place_id = Column(Integer, ForeignKey("users.id"))

    member_count = Column(Integer)

    best_triple_start = Column(Integer)
    best_triple_start_user_id = Column(Integer)

    longest_triple_streak = Column(Integer)
    longest_triple_user_id = Column(Integer)

    longest_qb_streak = Column(Integer)
    longest_rb_streak = Column(Integer)
    longest_wr_streak = Column(Integer)

    most_triples_in_season = Column(Integer)
    most_triples_user_id = Column(Integer)

    clinched_week = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
    UniqueConstraint("league_id", "season", "scope", name="uq_streak_history"),
    )

__all_models__ = [
    Season,               # Independent
    Team,                 # Independent
    User,                 # Independent, referenced by picks, leagues, members

    League,               # Requires User via created_by_user_id
    LeagueMember,         # Requires League, User
    LeagueSeasonMember,   # Requires League, User -- per-season participation
    LeagueInviteToken,    # Requires League
    LeagueSeasonFinance,
    LeagueSeasonMemberPayment, 

    Player,               # Depends on Team via team_id

    NFLGame,              # Independent, referenced by PlayerGameStat

    WeeklyPick,           # Depends on User, League
    PlayerGameStat,       # Depends on Player, NFLGame

    WeeklyScore,          # Depends on League
    PositionStreak,       # Depends on League
    AllPositionStreak,    # Depends on League

    StreakSeasonHistory   # Streak History stats Hub; depends on League but could be global
]
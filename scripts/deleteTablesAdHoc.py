import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import WeeklyScore, PositionStreak, AllPositionStreak

# Drop existing tables if they exist
WeeklyScore.__table__.drop(bind=engine, checkfirst=True)
PositionStreak.__table__.drop(bind=engine, checkfirst=True)
AllPositionStreak.__table__.drop(bind=engine, checkfirst=True)

# Recreate them using the latest model definitions (e.g., with league_id added)
WeeklyScore.__table__.create(bind=engine, checkfirst=True)
PositionStreak.__table__.create(bind=engine, checkfirst=True)
AllPositionStreak.__table__.create(bind=engine, checkfirst=True)

print("✅ Tables dropped and recreated with updated schema.")

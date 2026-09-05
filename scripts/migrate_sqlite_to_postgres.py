import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.database import Base
from app.models import __all_models__  # list of all your ORM models

# Load .env for DATABASE_URL or TEST_DATABASE_URL
load_dotenv()

# Connect to SQLite (local file)
sqlite_engine = create_engine("sqlite:///./test_fantasy.db")
SQLiteSession = sessionmaker(bind=sqlite_engine)
sqlite_db = SQLiteSession()

# Connect to Postgres (from env)
pg_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
PGSession = sessionmaker(bind=pg_engine)
pg_db = PGSession()

def copy_data(model):
    print(f"Copying: {model.__tablename__}")
    items = sqlite_db.query(model).all()
    for item in items:
        pg_db.merge(item)  # merge = upsert behavior
    pg_db.commit()

if __name__ == "__main__":
    for model in __all_models__:
        copy_data(model)
    print("✅ Migration complete.")

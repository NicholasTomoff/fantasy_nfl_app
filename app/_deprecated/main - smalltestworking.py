from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
import logging
from dotenv import load_dotenv
import uvicorn  # <-- make sure this is installed

app = FastAPI()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
logging.info(f"RUNTIME DB_URL: {DATABASE_URL}")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"ssl": False}  # ← force plain connection for asyncpg
)

@app.get("/")
async def root():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
        return {"db_test": value}
    except Exception as e:
        logging.exception("Failed in root route")
        return {"error": str(e)}

# 👇 This ensures app runs with correct host/port if started manually
if __name__ == "__main__":
    print("Starting on host:", os.getenv("HOST", "0.0.0.0"))
    print("Starting on port:", os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=8080)

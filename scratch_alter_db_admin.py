import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

async def alter():
    try:
        conn = await asyncpg.connect(db_url)
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;")
        await conn.close()
        print("Berhasil menambah kolom is_banned dan is_verified!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(alter())

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
        await conn.execute("ALTER TABLE perusahaan_profiles ALTER COLUMN ukuran TYPE VARCHAR(100);")
        await conn.close()
        print("Berhasil mengupdate batas karakter kolom ukuran!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(alter())

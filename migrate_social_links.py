"""
Migration script: Add social_links column to pelamar_profiles table.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pelamar_profiles' AND column_name='social_links'
        """))
        exists = result.fetchone()
        if not exists:
            await conn.execute(text("ALTER TABLE pelamar_profiles ADD COLUMN social_links TEXT"))
            print("OK: Kolom social_links berhasil ditambahkan ke tabel pelamar_profiles")
        else:
            print("INFO: Kolom social_links sudah ada, tidak perlu migrasi")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def migrate():
    engine = create_async_engine('postgresql+asyncpg://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres')
    async with engine.begin() as conn:
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR(6);'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP WITH TIME ZONE;'))
        await conn.execute(text('ALTER TABLE pelamar_profiles ADD COLUMN IF NOT EXISTS judul_posisi VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE pelamar_profiles ADD COLUMN IF NOT EXISTS keahlian TEXT;'))
        await conn.execute(text('ALTER TABLE pelamar_profiles ADD COLUMN IF NOT EXISTS sertifikasi TEXT;'))
        await conn.execute(text('ALTER TABLE pelamar_profiles ADD COLUMN IF NOT EXISTS pengalaman_kerja TEXT;'))
        await conn.execute(text('ALTER TABLE pelamar_profiles ADD COLUMN IF NOT EXISTS riwayat_pendidikan TEXT;'))
        await conn.execute(text('DROP TABLE IF EXISTS saved_jobs CASCADE;'))
        await conn.execute(text('''
            CREATE TABLE saved_jobs (
                id VARCHAR PRIMARY KEY,
                pelamar_id VARCHAR NOT NULL REFERENCES pelamar_profiles(id) ON DELETE CASCADE,
                job_id VARCHAR NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        '''))
    print('Migration complete')

if __name__ == '__main__':
    asyncio.run(migrate())

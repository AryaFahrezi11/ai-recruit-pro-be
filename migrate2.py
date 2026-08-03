import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def migrate():
    engine = create_async_engine('postgresql+asyncpg://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres')
    async with engine.begin() as conn:
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS nib_number VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS nib_document_url VARCHAR(500);'))
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS hr_name VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS hr_whatsapp VARCHAR(20);'))
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS hr_position VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE perusahaan_profiles ADD COLUMN IF NOT EXISTS hr_id_card_url VARCHAR(500);'))
    print('Migration complete')

if __name__ == '__main__':
    asyncio.run(migrate())

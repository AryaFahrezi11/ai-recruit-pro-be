import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres.vrzrmqclnuvwpyhmczao:Airecruitpro123@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text("UPDATE applications SET status='virtual_interview', video_url=NULL, ai_result=NULL WHERE status IN ('cv_screening', 'video_analysis', 'human_validation', 'video_uploaded')"))
        print(f"Berhasil me-reset {result.rowcount} kandidat kembali ke tahap 3. VIRTUAL INTERVIEW.")
    await engine.dispose()

asyncio.run(main())

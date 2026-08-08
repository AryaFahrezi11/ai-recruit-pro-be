import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres')
    res = await conn.fetch("SELECT id, status, perusahaan_id FROM job_postings")
    for r in res:
        print(f"{r['id']}: {r['status']} (perusahaan_id: {r['perusahaan_id']})")
    await conn.close()

asyncio.run(check())

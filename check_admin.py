import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres')
    res = await conn.fetch("SELECT email FROM users WHERE role = 'admin'")
    print("ADMIN USERS:")
    for row in res:
        print(row['email'])
    await conn.close()

asyncio.run(main())

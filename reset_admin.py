import asyncio
import asyncpg
import bcrypt

async def main():
    conn = await asyncpg.connect('postgresql://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(b"admin123", salt).decode('utf-8')
    await conn.execute("UPDATE users SET password_hash = $1 WHERE email = 'admin@airecruitpro.com'", hashed_password)
    print("Password reset to admin123")
    await conn.close()

asyncio.run(main())

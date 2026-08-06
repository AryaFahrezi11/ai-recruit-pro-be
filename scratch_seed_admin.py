import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.models.user import User
from app.core.security import hash_password

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(db_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_admin():
    async with AsyncSessionLocal() as db:
        email = "admin@airecruitpro.com"
        password = "admin"
        
        # Check if exists
        from sqlalchemy.future import select
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            new_admin = User(
                email=email,
                password_hash=hash_password(password),
                role="admin",
                is_active=True
            )
            db.add(new_admin)
            await db.commit()
            print(f"Admin account created! Email: {email} | Password: {password}")
        else:
            print("Admin account already exists.")

if __name__ == "__main__":
    asyncio.run(seed_admin())

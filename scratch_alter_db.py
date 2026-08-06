import asyncio
from app.core.database import engine, Base
from app.models.user import PerusahaanSettings

async def main():
    async with engine.begin() as conn:
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())

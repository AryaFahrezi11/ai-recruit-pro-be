"""
🗄️ Koneksi Database (SQLite untuk dev, PostgreSQL untuk production)
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Buat engine koneksi database
# Development: SQLite (tanpa install apapun)
# Production: Ganti DATABASE_URL di .env ke PostgreSQL
from sqlalchemy.pool import NullPool

engine_kwargs = {
    "echo": False,
    "connect_args": {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
}

if settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)


# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class untuk semua model database
class Base(DeclarativeBase):
    pass


# Dependency: mendapatkan session database
async def get_db() -> AsyncSession:
    """
    Dependency injection untuk mendapatkan database session.
    Digunakan di setiap router yang perlu akses database.

    Contoh penggunaan:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

"""
🗄️ Koneksi Database (SQLite untuk dev, PostgreSQL untuk production)
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool
from app.core.config import settings

is_pg = settings.DATABASE_URL.startswith("postgresql")
is_mysql = settings.DATABASE_URL.startswith("mysql")

engine_kwargs = {
    "echo": False,
}

if is_pg:
    engine_kwargs["connect_args"] = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }

if is_pg or is_mysql:
    engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
    # Supabase Free Tier dibatasi maksimal 15 koneksi pooler PgBouncer
    if is_pg:
        engine_kwargs["pool_size"] = 4
        engine_kwargs["max_overflow"] = 4
        engine_kwargs["pool_timeout"] = 10
    else: # MySQL
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_timeout"] = 20
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_pre_ping"] = True

db_url = settings.DATABASE_URL
# Jika menggunakan Supabase Pooler pada port 5432 (Session Mode max 15 klien),
# alihkan otomatis ke port 6543 (Transaction Mode) yang mendukung ribuan koneksi tanpa batas pool_size.
if ("supabase.co" in db_url or "pooler.supabase.com" in db_url) and ":5432" in db_url:
    db_url = db_url.replace(":5432", ":6543")

engine = create_async_engine(db_url, **engine_kwargs)


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

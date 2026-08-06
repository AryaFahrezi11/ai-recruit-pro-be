import asyncio
from sqlalchemy import text
from app.core.database import engine

async def alter_job_postings():
    async with engine.begin() as conn:
        print("Altering job_postings table...")
        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN department VARCHAR(100);"))
        except Exception as e:
            print(f"department failed (maybe exists): {e}")
            
        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN experience_level VARCHAR(100);"))
        except Exception as e:
            print(f"experience_level failed (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN benefits_json TEXT;"))
        except Exception as e:
            print(f"benefits_json failed (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN ai_keywords_json TEXT;"))
        except Exception as e:
            print(f"ai_keywords_json failed (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN video_questions_json TEXT;"))
        except Exception as e:
            print(f"video_questions_json failed (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE job_postings ADD COLUMN openings_count INTEGER DEFAULT 1;"))
        except Exception as e:
            print(f"openings_count failed (maybe exists): {e}")
            
        print("Done altering job_postings.")

if __name__ == "__main__":
    asyncio.run(alter_job_postings())

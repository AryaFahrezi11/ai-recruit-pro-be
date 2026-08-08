import asyncio
import asyncpg
import sys

async def run_migrations():
    print("Connecting to DB...")
    # URL string from .env
    dsn = "postgresql://postgres:Airecruitpro123@db.vrzrmqclnuvwpyhmczao.supabase.co:5432/postgres"
    
    conn = await asyncpg.connect(dsn)
    try:
        print("Running ALTER TABLE...")
        await conn.execute("""
            ALTER TABLE perusahaan_settings
            ADD COLUMN IF NOT EXISTS email_hire_body TEXT DEFAULT 'Halo {{candidate_name}}, Selamat! Kami dengan senang hati menawarkan Anda posisi {{job_title}} di {{company_name}}.',
            ADD COLUMN IF NOT EXISTS email_reject_subject VARCHAR DEFAULT '[AI Recruit Pro] Update Status Lamaran: {{job_title}}',
            ADD COLUMN IF NOT EXISTS email_reject_body TEXT DEFAULT 'Halo {{candidate_name}}, Terima kasih atas ketertarikan Anda pada posisi {{job_title}} di {{company_name}}. Sayangnya, saat ini kami memutuskan untuk melanjutkan dengan kandidat lain yang lebih sesuai.';
        """)
        print("Successfully added columns!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())

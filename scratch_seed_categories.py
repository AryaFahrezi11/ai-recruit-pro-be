import asyncio
from app.core.database import engine
from app.models.job import JobCategory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

CATEGORIES = [
    {"nama_kategori": "Software Engineering & IT", "deskripsi": "Pengembangan perangkat lunak, infrastruktur, dan IT."},
    {"nama_kategori": "Data Science & Analytics", "deskripsi": "Analisis data, machine learning, dan bisnis intelijen."},
    {"nama_kategori": "Design & Creative", "deskripsi": "UI/UX, desain grafis, dan industri kreatif."},
    {"nama_kategori": "Marketing & PR", "deskripsi": "Pemasaran digital, hubungan masyarakat, dan SEO."},
    {"nama_kategori": "Sales & Business Development", "deskripsi": "Penjualan, kemitraan strategis, dan pengembangan bisnis."},
    {"nama_kategori": "Human Resources", "deskripsi": "Rekrutmen, pengembangan organisasi, dan HR."},
    {"nama_kategori": "Finance & Accounting", "deskripsi": "Keuangan, akuntansi, dan audit."},
    {"nama_kategori": "Operations & Logistics", "deskripsi": "Manajemen operasional, supply chain, dan logistik."},
    {"nama_kategori": "Customer Service", "deskripsi": "Pelayanan pelanggan dan dukungan teknis."},
    {"nama_kategori": "Product Management", "deskripsi": "Manajemen produk dan strategi produk."}
]

async def seed_categories():
    async with AsyncSession(engine) as db:
        print("Seeding job categories...")
        for cat in CATEGORIES:
            result = await db.execute(select(JobCategory).where(JobCategory.nama_kategori == cat["nama_kategori"]))
            existing = result.scalars().first()
            if not existing:
                new_cat = JobCategory(nama_kategori=cat["nama_kategori"], deskripsi=cat["deskripsi"])
                db.add(new_cat)
        
        await db.commit()
        print("Done seeding job categories.")

if __name__ == "__main__":
    asyncio.run(seed_categories())

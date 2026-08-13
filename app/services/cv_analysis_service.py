"""
📄 CV Analysis Service
Logika bisnis untuk menganalisis CV pelamar terhadap Job Description.
"""
from starlette.concurrency import run_in_threadpool
from app.services.embedding_service import EmbeddingService
from app.utils.pdf_extractor import extract_text_from_pdf, clean_text


class CVAnalysisService:
    """
    Service untuk menjalankan proses analisis CV:
    1. Ekstrak teks dari file CV (PDF/TXT)
    2. Bersihkan teks (preprocessing)
    3. Bandingkan dengan Job Description menggunakan SBERT
    4. Kembalikan hasil skor dan keputusan
    """

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service


    async def analyze_match_from_embeddings(
        self,
        cv_embedding: list[float],
        jd_embedding: list[float],
        threshold: float = None,
        cv_text: str = None,
        ai_keywords: list[str] = None,
    ) -> dict:
        """
        Menganalisis kecocokan secara langsung menggunakan vektor yang sudah ada.
        """
        result = await run_in_threadpool(
            self.embedding_service.analyze_match_from_embeddings,
            cv_embedding=cv_embedding,
            jd_embedding=jd_embedding,
            threshold=threshold,
            cv_text=cv_text,
            ai_keywords=ai_keywords,
        )
        return result

    async def analyze_cv(
        self,
        cv_text: str,
        job_description: str,
        threshold: float = None,
        ai_keywords: list[str] = None,
    ) -> dict:
        """
        Menganalisis kecocokan CV dengan Job Description.

        Args:
            cv_text: Teks CV yang sudah diekstrak
            job_description: Teks Job Description
            threshold: Ambang batas kelulusan (opsional)

        Returns:
            dict: Hasil analisis lengkap
        """
        # Bersihkan teks
        cleaned_cv = clean_text(cv_text)
        cleaned_jd = clean_text(job_description)

        # Jalankan analisis AI di thread terpisah agar tidak memblokir event loop
        result = await run_in_threadpool(
            self.embedding_service.analyze_match,
            text_cv=cleaned_cv,
            text_jd=cleaned_jd,
            threshold=threshold,
            ai_keywords=ai_keywords,
        )

        return result

    async def process_cv_file(
        self,
        file_content: bytes,
        file_type: str,
        job_description: str,
        threshold: float = None,
    ) -> dict:
        """
        Memproses file CV dari upload hingga hasil analisis.

        Args:
            file_content: Konten file dalam bytes
            file_type: Tipe file (pdf/txt)
            job_description: Teks Job Description
            threshold: Ambang batas kelulusan

        Returns:
            dict: Hasil analisis + teks yang diekstrak
        """
        # Ekstrak teks berdasarkan tipe file
        if file_type == "pdf":
            raw_text = extract_text_from_pdf(file_content)
        elif file_type == "txt":
            raw_text = file_content.decode("utf-8")
        else:
            raise ValueError(f"Tipe file '{file_type}' tidak didukung")

        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("Teks CV terlalu pendek atau tidak bisa diekstrak")

        # Analisis CV
        result = await self.analyze_cv(
            cv_text=raw_text,
            job_description=job_description,
            threshold=threshold,
        )

        result["extracted_text"] = raw_text
        result["cleaned_text"] = clean_text(raw_text)

        return result

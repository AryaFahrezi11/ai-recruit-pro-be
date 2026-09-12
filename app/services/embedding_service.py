"""
🧠 Embedding Service
Memuat dan mengelola model SBERT untuk menghasilkan vektor embedding.
Model dimuat SEKALI saat server start, lalu digunakan terus-menerus.
"""
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings


def check_education_eligibility(cv_edu: str, job_edu: str) -> bool:
    if not job_edu or str(job_edu).strip() in ["", "-", "None"]:
        return True
    
    mapping = {
        "S3/Doktor": 5, "S2/Master": 4, "S1/Sarjana": 3, 
        "D3/Diploma": 2, "SMA/SMK": 1, "-": 0
    }
    
    from app.utils.pdf_extractor import extract_education
    if cv_edu not in mapping:
        cv_edu = extract_education(str(cv_edu))
    if job_edu not in mapping:
        job_edu = extract_education(str(job_edu))
    
    cv_score = mapping.get(cv_edu, 0)
    job_score = mapping.get(job_edu, 0)
    
    if job_score == 0:
        return True
    if cv_score < job_score:
        return False
    return True


def evaluate_text_completeness(cv_text: str = None, jd_text: str = None, ai_keywords: list[str] = None):
    """
    Memeriksa kelengkapan teks dari kedua sisi:
    1. Dokumen CV pelamar (cv_document / extracted_text)
    2. Informasi lowongan pekerjaan (job_postings / deskripsi, kualifikasi, tanggung jawab, kolom json)
    
    Jika salah satu atau keduanya kurang lengkap / sedikit karakternya,
    sistem tidak menghitung dengan formula normal melainkan memberikan skor rendah dan keterangan jelas.
    """
    issues = []
    cv_len = len(cv_text.strip()) if cv_text else 0
    jd_len = len(jd_text.strip()) if jd_text else 0
    cv_words = len(cv_text.split()) if cv_text else 0
    jd_words = len(jd_text.split()) if jd_text else 0

    # Ambang batas minimum karakter & kata untuk deskripsi yang memadai
    MIN_CHARS = 150
    MIN_WORDS = 25

    is_cv_short = (cv_text is None or cv_len < MIN_CHARS or cv_words < MIN_WORDS)
    is_jd_short = (jd_text is None or jd_len < MIN_CHARS or jd_words < MIN_WORDS)
    is_keywords_empty = (ai_keywords is not None and len(ai_keywords) == 0)

    if is_cv_short:
        issues.append(
            f"Deskripsi dokumen CV pelamar kurang lengkap atau memiliki karakter terlalu sedikit ({cv_len} karakter). Harap lampirkan CV dengan uraian pengalaman kerja, keahlian, dan riwayat pendidikan yang lebih detail."
        )

    if is_jd_short:
        issues.append(
            f"Uraian deskripsi pekerjaan atau kualifikasi posisi lowongan pekerjaan kurang lengkap/terlalu singkat ({jd_len} karakter)."
        )

    if is_keywords_empty:
        issues.append(
            "Kolom spesifikasi keahlian (ai_keywords) pada lowongan pekerjaan belum terisi secara lengkap."
        )

    if is_cv_short or is_jd_short:
        keterangan_gabungan = " | ".join(issues)
        return False, keterangan_gabungan, {
            "status_kelengkapan": "kurang_lengkap",
            "keterangan": keterangan_gabungan,
            "cv_char_count": cv_len,
            "jd_char_count": jd_len,
            "cv_word_count": cv_words,
            "jd_word_count": jd_words,
            "is_cv_complete": not is_cv_short,
            "is_jd_complete": not is_jd_short,
        }

    keterangan_sukses = (
        "Deskripsi dokumen CV dan rincian lowongan pekerjaan lengkap. Skor dihitung secara objektif menggunakan formula AI (60% kesesuaian semantik SBERT + 40% pemenuhan keahlian wajib)."
    )
    return True, keterangan_sukses, {
        "status_kelengkapan": "lengkap",
        "keterangan": keterangan_sukses,
        "cv_char_count": cv_len,
        "jd_char_count": jd_len,
        "cv_word_count": cv_words,
        "jd_word_count": jd_words,
        "is_cv_complete": True,
        "is_jd_complete": True,
    }


class EmbeddingService:
    """
    Service untuk mengelola model SBERT dan menghasilkan embedding.

    Model: paraphrase-multilingual-MiniLM-L12-v2
    - Mendukung 50+ bahasa (termasuk Indonesia)
    - Dimensi embedding: 384
    - Ukuran: ~471 MB
    """

    def __init__(self):
        """Memuat model SBERT ke RAM."""
        self.model_name = settings.SBERT_MODEL_NAME
        print(f"[INFO] Loading model: {self.model_name}")
        start = time.time()
        self.model = SentenceTransformer(self.model_name)
        elapsed = time.time() - start
        print(f"[OK] Model dimuat dalam {elapsed:.2f} detik")
        print(f"[INFO] Dimensi embedding: {self.model.get_sentence_embedding_dimension()}")

    def get_embedding(self, text: str) -> list[float]:
        """
        Mengubah teks menjadi vektor embedding 384 dimensi.

        Args:
            text: Teks yang akan di-embed (CV atau Job Description)

        Returns:
            List[float]: Vektor embedding 384 dimensi
        """
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding[0].tolist()

    def calculate_similarity(self, embedding_a: list[float], embedding_b: list[float]) -> float:
        """
        Menghitung Cosine Similarity antara dua vektor embedding.

        Args:
            embedding_a: Vektor embedding pertama (misal: CV)
            embedding_b: Vektor embedding kedua (misal: Job Description)

        Returns:
            float: Skor similarity (0.0 - 1.0)
        """
        vec_a = np.array(embedding_a).reshape(1, -1)
        vec_b = np.array(embedding_b).reshape(1, -1)
        similarity = cosine_similarity(vec_a, vec_b)[0][0]
        return float(similarity)


    def analyze_match_from_embeddings(
        self,
        cv_embedding: list[float],
        jd_embedding: list[float],
        threshold: float = None,
        cv_text: str = None,
        jd_text: str = None,
        ai_keywords: list[str] = None,
        cv_education: str = None,
        job_education: str = None
    ) -> dict:
        if threshold is None:
            threshold = settings.CV_THRESHOLD_DEFAULT

        start_time = time.time()

        # 1. Evaluasi kelengkapan teks & jumlah karakter dari kedua sisi
        is_complete, keterangan, kelengkapan_meta = evaluate_text_completeness(
            cv_text=cv_text,
            jd_text=jd_text,
            ai_keywords=ai_keywords
        )

        # Jika deskripsi salah satu atau kedua pihak tidak lengkap / sedikit karakter:
        # Berikan nilai rendah dan jangan hitung dengan rumus normal.
        if not is_complete:
            elapsed = (time.time() - start_time) * 1000
            skor_rendah = 20.0  # Nilai rendah untuk input tidak lengkap
            similarity_rendah = 0.20

            return {
                "cosine_similarity_score": similarity_rendah,
                "skor_kecocokan": skor_rendah,
                "threshold_digunakan": threshold,
                "kategori": "tidak_cocok",
                "hasil": "ditolak",
                "waktu_proses_ms": round(elapsed, 2),
                "hybrid_details": {
                    **kelengkapan_meta,
                    "sbert_score": skor_rendah,
                    "keyword_score": 0.0,
                    "keywords_found": 0,
                    "keywords_total": len(ai_keywords) if ai_keywords else 0,
                }
            }

        # 2. Jika deskripsi banyak dan kalimat memadai, baru hitung sesuai rumus normal
        similarity = self.calculate_similarity(cv_embedding, jd_embedding)
        sbert_skor = similarity * 100
        
        # Hitung Keyword Matching (Hybrid)
        keyword_skor = 0.0
        skor_hybrid = sbert_skor
        found_count = 0
        
        if ai_keywords and len(ai_keywords) > 0 and cv_text:
            cv_text_lower = cv_text.lower()
            found_count = sum(1 for kw in ai_keywords if kw.lower() in cv_text_lower)
            keyword_skor = (found_count / len(ai_keywords)) * 100
            
            # Pembobotan: 60% SBERT, 40% Keyword
            skor_hybrid = (sbert_skor * 0.6) + (keyword_skor * 0.4)
            
        skor = round(skor_hybrid, 2)

        # Kategorisasi
        if skor >= 70:
            kategori = "sangat_cocok"
        elif skor >= 55:
            kategori = "cocok"
        elif skor >= 40:
            kategori = "cukup_cocok"
        elif skor >= 25:
            kategori = "kurang_cocok"
        else:
            kategori = "tidak_cocok"

        hasil = "lolos" if skor >= threshold else "ditolak"
        
        # Override hasil if education is not eligible
        is_edu_eligible = True
        if cv_education and job_education:
            is_edu_eligible = check_education_eligibility(cv_education, job_education)
            if not is_edu_eligible:
                hasil = "ditolak"
                kategori = "tidak_memenuhi_syarat_pendidikan"
                kelengkapan_meta["keterangan"] += " (Catatan: Jenjang pendidikan pelamar belum memenuhi kualifikasi minimal posisi)."

        elapsed = (time.time() - start_time) * 1000

        return {
            "cosine_similarity_score": float(similarity),
            "skor_kecocokan": skor,
            "threshold_digunakan": threshold,
            "kategori": kategori,
            "hasil": hasil,
            "waktu_proses_ms": round(elapsed, 2),
            "hybrid_details": {
                **kelengkapan_meta,
                "sbert_score": round(sbert_skor, 2),
                "keyword_score": round(keyword_skor, 2),
                "keywords_found": found_count,
                "keywords_total": len(ai_keywords) if ai_keywords else 0
            }
        }

    def analyze_match(
        self,
        text_cv: str,
        text_jd: str,
        threshold: float = None,
        ai_keywords: list[str] = None,
        cv_education: str = None,
        job_education: str = None
    ) -> dict:
        """
        Menganalisis kecocokan CV dengan Job Description secara langsung.
        Fungsi ini menggabungkan embedding + similarity dalam satu langkah.

        Args:
            text_cv: Teks CV pelamar
            text_jd: Teks Job Description
            threshold: Ambang batas kelulusan (default dari config)
            ai_keywords: Daftar keahlian spesifik untuk Hybrid Search
            cv_education: Pendidikan tertinggi pelamar
            job_education: Pendidikan minimal posisi

        Returns:
            dict: Hasil analisis lengkap
        """
        if threshold is None:
            threshold = settings.CV_THRESHOLD_DEFAULT

        start_time = time.time()

        # 1. Evaluasi kelengkapan teks & jumlah karakter dari kedua sisi
        is_complete, keterangan, kelengkapan_meta = evaluate_text_completeness(
            cv_text=text_cv,
            jd_text=text_jd,
            ai_keywords=ai_keywords
        )

        # Jika salah satu atau keduanya kurang lengkap / sedikit karakter:
        if not is_complete:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            skor_rendah = 20.0
            return {
                "cosine_similarity_score": 0.20,
                "skor_kecocokan": skor_rendah,
                "threshold_digunakan": threshold,
                "kategori": "tidak_cocok",
                "hasil": "gagal",
                "model_ai": self.model_name,
                "waktu_proses_ms": elapsed_ms,
                "hybrid_details": {
                    **kelengkapan_meta,
                    "sbert_score": skor_rendah,
                    "keyword_score": 0.0,
                    "keywords_found": 0,
                    "keywords_total": len(ai_keywords) if ai_keywords else 0
                }
            }

        # 2. Jika deskripsi lengkap dan panjang kalimat memadai, baru hitung sesuai rumus
        # Generate embeddings
        cv_embedding = self.get_embedding(text_cv)
        jd_embedding = self.get_embedding(text_jd)

        # Hitung similarity SBERT
        similarity = self.calculate_similarity(cv_embedding, jd_embedding)
        sbert_skor = similarity * 100
        
        # Hitung Keyword Matching (Hybrid)
        keyword_skor = 0.0
        skor_hybrid = sbert_skor
        found_count = 0
        
        if ai_keywords and len(ai_keywords) > 0 and text_cv:
            cv_text_lower = text_cv.lower()
            found_count = sum(1 for kw in ai_keywords if kw.lower() in cv_text_lower)
            keyword_skor = (found_count / len(ai_keywords)) * 100
            
            # Pembobotan: 60% SBERT, 40% Keyword
            skor_hybrid = (sbert_skor * 0.6) + (keyword_skor * 0.4)
            
        skor = round(skor_hybrid, 2)

        # Kategorisasi
        if skor >= 70:
            kategori = "sangat_cocok"
        elif skor >= 55:
            kategori = "cocok"
        elif skor >= 40:
            kategori = "cukup_cocok"
        elif skor >= 25:
            kategori = "kurang_cocok"
        else:
            kategori = "tidak_cocok"

        # Keputusan
        hasil = "lolos" if skor >= threshold else "gagal"
        
        # Override hasil if education is not eligible
        is_edu_eligible = True
        if cv_education and job_education:
            is_edu_eligible = check_education_eligibility(cv_education, job_education)
            if not is_edu_eligible:
                hasil = "gagal"
                kategori = "tidak_memenuhi_syarat_pendidikan"
                kelengkapan_meta["keterangan"] += " (Catatan: Jenjang pendidikan pelamar belum memenuhi kualifikasi minimal posisi)."

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "cosine_similarity_score": round(similarity, 6),
            "skor_kecocokan": skor,
            "threshold_digunakan": threshold,
            "kategori": kategori,
            "hasil": hasil,
            "model_ai": self.model_name,
            "waktu_proses_ms": elapsed_ms,
            "cv_embedding": cv_embedding,
            "jd_embedding": jd_embedding,
            "hybrid_details": {
                **kelengkapan_meta,
                "sbert_score": round(sbert_skor, 2),
                "keyword_score": round(keyword_skor, 2),
                "keywords_found": found_count,
                "keywords_total": len(ai_keywords) if ai_keywords else 0
            }
        }

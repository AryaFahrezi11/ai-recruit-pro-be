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
        print(f"⏳ Loading model: {self.model_name}")
        start = time.time()
        self.model = SentenceTransformer(self.model_name)
        elapsed = time.time() - start
        print(f"✅ Model dimuat dalam {elapsed:.2f} detik")
        print(f"📐 Dimensi embedding: {self.model.get_sentence_embedding_dimension()}")

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

    def analyze_match(self, text_cv: str, text_jd: str, threshold: float = None) -> dict:
        """
        Menganalisis kecocokan CV dengan Job Description secara langsung.
        Fungsi ini menggabungkan embedding + similarity dalam satu langkah.

        Args:
            text_cv: Teks CV pelamar
            text_jd: Teks Job Description
            threshold: Ambang batas kelulusan (default dari config)

        Returns:
            dict: Hasil analisis lengkap
        """
        if threshold is None:
            threshold = settings.CV_THRESHOLD_DEFAULT

        start_time = time.time()

        # Generate embeddings
        cv_embedding = self.get_embedding(text_cv)
        jd_embedding = self.get_embedding(text_jd)

        # Hitung similarity
        similarity = self.calculate_similarity(cv_embedding, jd_embedding)
        skor = round(similarity * 100, 2)

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
        }

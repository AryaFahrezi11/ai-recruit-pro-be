"""
🔧 PDF Extractor & Text Cleaning Utilities (With OCR & Parsers)
"""
import re
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Konfigurasi Tesseract (sesuaikan dengan OS/Environment)
# Jika di Windows, biasanya: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(file_content: bytes) -> tuple[str, bool]:
    """
    Mengekstrak teks dari file PDF (mendukung OCR).
    
    Returns:
        tuple(str, bool): Teks hasil ekstraksi dan status apakah OCR digunakan
    """
    full_text = ""
    is_ocr_used = False
    
    try:
        # Buka dokumen dari memory
        doc = fitz.open(stream=file_content, filetype="pdf")
        
        for page in doc:
            # Ekstrak teks secara langsung
            text = page.get_text("text").strip()
            
            # Jika teks kosong (gambar/scan), jalankan OCR
            if not text or len(text) < 20:
                is_ocr_used = True
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                try:
                    text = pytesseract.image_to_string(img, lang='eng+ind')
                except Exception as e:
                    print(f"[OCR Warning] Gagal membaca gambar halaman: {e}")
                    text = ""
            
            full_text += text + "\n"
            
    except Exception as e:
        print(f"[PDF Warning] Gagal membaca PDF: {e}")
        return "", False
        
    return full_text.strip(), is_ocr_used


def extract_contact(text: str) -> dict:
    """Mengekstrak kontak email dan nomor HP."""
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone = re.search(r'(?:\+62|62|08)\s?[\d-]{9,13}', text)
    
    return {
        "email": email.group(0) if email else "-",
        "phone": phone.group(0) if phone else "-"
    }


def extract_education(text: str) -> str:
    """Mendeteksi level pendidikan tertinggi (S1/S2/S3/SMA dll)."""
    text_lower = text.lower()
    highest_score = 0
    
    patterns = [
        (5, r'\b(ph\.?d|doktor|doctor|dr\.|s3)\b'),
        (4, r'\b(magister|master|m\.?ba|m\.?kom|m\.?t|m\.?si|m\.?sc|s2)\b'),
        (3, r'\b(sarjana|bachelor|s\.?kom|s\.?t|s\.?e|s\.?pd|s\.?sos|b\.?sc|b\.?a|s1)\b'),
        (2, r'\b(diploma|d3|d4|a\.?md)\b'),
        (1, r'\b(sma|smk|slta|stm)\b')
    ]
    
    for score, pattern in patterns:
        if re.search(pattern, text_lower) and score > highest_score:
            highest_score = score
            
    mapping = {
        5: "S3/Doktor", 4: "S2/Master", 3: "S1/Sarjana", 
        2: "D3/Diploma", 1: "SMA/SMK", 0: "-"
    }
    return mapping[highest_score]


def clean_text(text: str) -> str:
    """
    Membersihkan teks dari karakter yang tidak diperlukan.
    """
    if not text:
        return ""
        
    # Hapus karakter non-printable
    text = re.sub(r'[^\x20-\x7E\u00C0-\u024F\u1E00-\u1EFF\u0080-\u00FF\n]', ' ', text)

    # Hapus multiple whitespace (tapi pertahankan newline)
    text = re.sub(r'[^\S\n]+', ' ', text)

    # Hapus baris kosong berlebih
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

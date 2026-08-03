"""
🔧 PDF Extractor & Text Cleaning Utilities
"""
import re
import io
import PyPDF2


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Mengekstrak teks dari file PDF.

    Args:
        file_content: Konten file PDF dalam bytes

    Returns:
        str: Teks hasil ekstraksi
    """
    reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def clean_text(text: str) -> str:
    """
    Membersihkan teks dari karakter yang tidak diperlukan.

    Args:
        text: Teks mentah

    Returns:
        str: Teks yang sudah dibersihkan
    """
    # Hapus karakter non-printable
    text = re.sub(r'[^\x20-\x7E\u00C0-\u024F\u1E00-\u1EFF\u0080-\u00FF\n]', ' ', text)

    # Hapus multiple whitespace (tapi pertahankan newline)
    text = re.sub(r'[^\S\n]+', ' ', text)

    # Hapus baris kosong berlebih
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

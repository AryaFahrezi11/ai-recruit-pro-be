"""
🛣️ Analysis Router - ENDPOINT UTAMA AI
Endpoint: /api/analysis
"""
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException

from app.schemas.analysis import CVAnalysisRequest, CVAnalysisResponse, CVUploadAnalysisResponse
from app.services.cv_analysis_service import CVAnalysisService

router = APIRouter()


@router.post("/cv/text", response_model=CVAnalysisResponse)
async def analyze_cv_text(req: CVAnalysisRequest, request: Request):
    """
    🧠 Analisis CV dari teks langsung.
    Bandingkan teks CV dengan Job Description menggunakan SBERT + Cosine Similarity.

    Cocok untuk testing cepat tanpa upload file.
    """
    embedding_service = request.app.state.embedding_service
    cv_service = CVAnalysisService(embedding_service)

    result = await cv_service.analyze_cv(
        cv_text=req.cv_text,
        job_description=req.job_description,
        threshold=req.threshold,
    )

    # Hapus embedding dari response (terlalu besar)
    result.pop("cv_embedding", None)
    result.pop("jd_embedding", None)

    return result


@router.post("/cv/upload", response_model=CVUploadAnalysisResponse)
async def analyze_cv_upload(
    request: Request,
    file: UploadFile = File(..., description="File CV (PDF atau TXT)"),
    job_description: str = Form(..., description="Teks Job Description"),
    threshold: float = Form(default=None, description="Threshold kelulusan (opsional)"),
):
    """
    🧠 Analisis CV dari file yang diupload.
    Upload file CV (PDF/TXT) dan bandingkan dengan Job Description.
    """
    # Validasi tipe file
    allowed_types = ["application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file '{file.content_type}' tidak didukung. Gunakan PDF atau TXT."
        )

    # Baca file
    file_content = await file.read()

    # Tentukan tipe
    file_type = "pdf" if file.content_type == "application/pdf" else "txt"

    # Jalankan analisis
    embedding_service = request.app.state.embedding_service
    cv_service = CVAnalysisService(embedding_service)

    try:
        result = await cv_service.process_cv_file(
            file_content=file_content,
            file_type=file_type,
            job_description=job_description,
            threshold=threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Format response
    extracted_text = result.pop("extracted_text", "")
    result.pop("cleaned_text", None)
    result.pop("cv_embedding", None)
    result.pop("jd_embedding", None)

    return {
        **result,
        "extracted_text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
        "jumlah_karakter": len(extracted_text),
    }

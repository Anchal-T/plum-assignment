import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.services.document_processor import DocumentProcessingError, DocumentProcessor
from app.services.llm_service import LLMService

router = APIRouter(prefix="/documents")

_SUFFIX_MAP = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
}

_processor = DocumentProcessor()
_llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)


@router.post("/process")
async def process_document(file: UploadFile = File(...)) -> dict:
    if file.content_type not in _SUFFIX_MAP:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds size limit")

    suffix = _SUFFIX_MAP[file.content_type]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        raw_text = _processor.extract_text(tmp_path, file.content_type)
        extracted = await _llm.extract_fields(raw_text, file.content_type)
        return extracted.to_dict()
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        os.unlink(tmp_path)

"""Document text extraction. Gracefully degrades when OCR tools are unavailable."""

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}


class DocumentProcessingError(Exception):
    pass


class DocumentProcessor:
    """Extracts raw text from uploaded files.

    Uses Tesseract for images, pdfplumber for text-based PDFs.
    Falls back gracefully when tools are not installed.
    """

    def extract_text(self, file_path: str, mime_type: str) -> str:
        if mime_type not in SUPPORTED_MIME:
            raise DocumentProcessingError(f"Unsupported file type: {mime_type}")

        path = Path(file_path)
        if not path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")

        if mime_type == "application/pdf":
            return self._extract_pdf(path)
        return self._extract_image(path)

    def _extract_pdf(self, path: Path) -> str:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            text = "\n".join(text_parts)
            if len(text.strip()) < 50:
                return self._extract_image(path)
            return text
        except ImportError:
            logger.warning("pdfplumber not installed, trying OCR fallback")
            return self._extract_image(path)
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            return ""

    def _extract_image(self, path: Path) -> str:
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(path)
            img = img.convert("L")
            return pytesseract.image_to_string(img, lang="eng", config="--oem 3 --psm 6")
        except ImportError:
            logger.warning("PIL/pytesseract not installed, returning empty text")
            return ""
        except Exception as e:
            logger.error("Image OCR failed: %s", e)
            return ""

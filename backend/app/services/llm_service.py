"""LLM-based structured data extraction from medical document text."""

import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical document data extraction assistant for an insurance company.
Given raw OCR text from a medical document, extract structured fields accurately.
If a field is not clearly present, set it to null rather than guessing.
Return a confidence score (0.0-1.0) based on text quality and extraction certainty."""

EXTRACTION_PROMPT = """Extract structured data from this medical document text.

Document text:
---
{raw_text}
---

Determine the document type (prescription, bill, diagnostic_report, pharmacy_bill)
and extract all relevant fields. Return JSON matching:
{{
  "doc_type": "...",
  "fields": {{ ... }},
  "confidence": 0.0-1.0,
  "warnings": []
}}

For prescriptions: doctor_name, doctor_reg, diagnosis, medicines,
tests_prescribed, patient_name, patient_age, date.

For bills: hospital_name, bill_number, date, patient_name,
line_items (description + amount + category), total.

For diagnostic reports: lab_name, patient_name, doctor_name, date,
tests (name + result + normal_range + is_abnormal).

For pharmacy bills: pharmacy_name, patient_name, doctor_name, date,
medicines (name + batch + qty + mrp + amount), total."""


class ExtractionError(Exception):
    pass


class ExtractedDocument:
    def __init__(self, doc_type: str, fields: dict, confidence: float, warnings: list[str] | None = None):
        self.doc_type = doc_type
        self.fields = fields
        self.confidence = confidence
        self.warnings = warnings or []

    def to_dict(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "fields": self.fields,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedDocument":
        return cls(
            doc_type=data.get("doc_type", "unknown"),
            fields=data.get("fields", {}),
            confidence=data.get("confidence", 0.0),
            warnings=data.get("warnings", []),
        )


class LLMService:
    """Uses OpenAI GPT-4o to extract structured data from OCR text.

    Falls back to a basic text parser if OpenAI is unavailable.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except Exception:
                pass
        return self._client

    async def extract_fields(self, raw_text: str, mime_type: str = "") -> ExtractedDocument:
        if self.client:
            try:
                return await self._extract_with_llm(raw_text)
            except Exception as e:
                logger.warning("LLM extraction failed: %s", e)
        return self._fallback_extract(raw_text, mime_type)

    async def _extract_with_llm(self, raw_text: str) -> ExtractedDocument:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_PROMPT.format(raw_text=raw_text[:10000])},
            ],
            temperature=0.1,
            max_tokens=2000,
            timeout=30,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return ExtractedDocument.from_dict(parsed)

    def _fallback_extract(self, raw_text: str, mime_type: str) -> ExtractedDocument:
        fields = {"raw_text_preview": raw_text[:500]}
        doc_type = "prescription" if any(k in raw_text.lower() for k in ["rx", "diagnosis", "dr."]) else "bill"
        return ExtractedDocument(
            doc_type=doc_type,
            fields=fields,
            confidence=0.3,
            warnings=["LLM unavailable, basic extraction used"],
        )

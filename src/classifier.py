"""
DocGraph - Document Classification & Structured Schema Extraction
Strictly enforces known categories with 'Miscellaneous' as the fallback bucket.
"""

import json
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import ollama

from src.config import OLLAMA_HOST, LLM_MODEL, get_active_categories


class DocumentMetadata(BaseModel):
    category: str = Field(description="Primary category of the document.")
    document_type: str = Field(
        description="Specific document type in PascalCase, e.g. LeaseAgreement, Passport, TaxCertificate."
    )
    issuer: str = Field(
        description="The organization, company, or person who issued the document."
    )
    document_date: Optional[str] = Field(
        default=None,
        description="Date of the document in YYYY-MM-DD format, or UNKNOWN if undetermined.",
    )
    canonical_filename: str = Field(
        description="Standardized filename: YYYY-MM-DD_Category_Issuer_DocType.ext"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        active = get_active_categories()
        for cat in active:
            if cat.lower() == value.lower():
                return cat
        return "Miscellaneous"


def sanitize_filename(filename: str) -> str:
    """Ensure safe characters for file names across filesystems."""
    filename = re.sub(r'[\\/*?:"<>| ]', "_", filename)
    filename = re.sub(r"_+", "_", filename)
    return filename


def classify_document(text: str, original_filename: str = "document.pdf") -> DocumentMetadata:
    client = ollama.Client(host=OLLAMA_HOST)
    categories = get_active_categories()

    ext = original_filename.split(".")[-1].lower() if "." in original_filename else "pdf"
    snippet = text[:3500]

    prompt = (
        f"You are a strict personal document classifier.\n"
        f"Analyze the following document text and return structured JSON matching the schema.\n\n"
        f"Allowed categories:\n"
        f"{', '.join(categories)}\n\n"
        f"Rules:\n"
        f"1. Choose the category strictly from the allowed list. If it does not fit, use 'Miscellaneous'.\n"
        f"2. Format document_date strictly as YYYY-MM-DD, or 'UNKNOWN' if no date is found.\n"
        f"3. Make issuer alphanumeric without spaces (PascalCase or snake_case).\n"
        f"4. Format canonical_filename as: <Date>_<Category>_<Issuer>_<DocumentType>.{ext}\n\n"
        f"Document text:\n\"\"\"\n{snippet}\n\"\"\""
    )

    # Pass the Pydantic schema directly into Ollama to enforce exact JSON structure
    response = client.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise document categorization engine. You only reply with structured JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        format=DocumentMetadata.model_json_schema(),
        options={"temperature": 0.0},
    )

    data = json.loads(response.message.content)

    # Sanitize the output filename
    canonical = sanitize_filename(data.get("canonical_filename", f"doc_archive.{ext}"))
    if not canonical.lower().endswith(f".{ext}"):
        canonical = f"{canonical.rsplit('.', 1)[0]}.{ext}"
    data["canonical_filename"] = canonical

    return DocumentMetadata(**data)

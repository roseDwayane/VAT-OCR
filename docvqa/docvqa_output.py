from typing import Optional, Literal
from pydantic import BaseModel
from ollama import chat
import base64
import sys
from pathlib import Path


def img_to_b64(path: str) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    return base64.b64encode(p.read_bytes()).decode("utf-8")


class Header(BaseModel):
    InvoiceYear: Optional[str] = None
    InvoiceMonth: Optional[str] = None
    InvoiceDay: Optional[str] = None
    PrefixTwoLetters: Optional[str] = None
    InvoiceNumber: Optional[str] = None
    BuyerTaxIDNumber: Optional[str] = None


class Tail(BaseModel):
    SalesTotalAmount: Optional[str] = None
    SalesTax: Optional[str] = None
    TotalAmount: Optional[str] = None


class ExtractedDoc(BaseModel):
    doc_class: Literal[
        'business_invoice', 'customs_tax_payment', 'e_invoice',
        'plumb_payment_order', 'tele_payment_order', 'tradition_invoice',
        'triple_invoice', 'triple_receipt', 'other'
    ]
    confidence: float
    header: Header | None = None
    tail: Tail | None = None
    notes: Optional[str] = None


if __name__ == "__main__":
    # Prefer CLI arg for image path; fall back to sample
    img_path = sys.argv[1] if len(sys.argv) > 1 else "./few_shot_sample/image/1_business_invoice.jpg"

    b64 = img_to_b64(img_path)

    system_msg = (
        "You are a document understanding assistant. "
        "Classify the document and extract fields. Return only valid JSON matching the provided schema. "
        "Use null for any field you cannot find; do not fabricate values."
    )

    user_msg = (
        "Task: 1) Choose doc_class from {business_invoice, customs_tax_payment, receipt, id_card, other}. "
        "2) Extract header/tail fields where applicable. "
        "3) Provide a confidence in [0,1]. "
        "If unsure about a value, set it to null."
    )

    schema = ExtractedDoc.model_json_schema()

    resp = chat(
        model='qwen2.5vl:7b',
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg, "images": [b64]},
        ],
        format=schema,
        options={"temperature": 0, "seed": 42},
    )

    print(resp.message.content)


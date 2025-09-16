from typing import Optional, Literal, Annotated
from pydantic import BaseModel, Field
from ollama import chat
import base64
import sys
import json
from pathlib import Path


def img_to_b64(path: str) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    return base64.b64encode(p.read_bytes()).decode("utf-8")

GENERATION_SCHEMA = {
  "type": "object",
  "properties": {
    "doc_class": {"type": "string", "enum": ["business_invoice","customs_tax_payment","receipt","id_card","other"]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "header": {
      "type": "object",
      "properties": {
        "InvoiceYear":       {"type":"string","pattern":"^(19|20)\\d{2}$"},
        "InvoiceMonth":      {"type":"string","pattern":"^(0[1-9]|1[0-2])$"},
        "InvoiceDay":        {"type":"string","pattern":"^(0[1-9]|[12]\\d|3[01])$"},
        "PrefixTwoLetters":  {"type":"string","pattern":"^[A-Z]{2}$"},
        "InvoiceNumber":     {"type":"string","pattern":"^\\d{8}$"},
        "BuyerTaxIDNumber":  {"type":"string","pattern":"^\\d{8}$"}
      },
      "additionalProperties": False
    },
    "tail": {
      "type": "object",
      "properties": {
        "SalesTotalAmount":  {"type":"string","pattern":"^\\d{1,12}$"},
        "SalesTax":          {"type":"string","pattern":"^\\d{1,12}$"},
        "TotalAmount":       {"type":"string","pattern":"^\\d{1,12}$"}
      },
      "additionalProperties": False
    },
    "notes": {"type":"string"}
  },
  "required": ["doc_class","confidence"],
  "additionalProperties": False
}


def _extract_first_json_block(text: str) -> str:
    depth = 0
    start = -1
    for i, ch in enumerate(text or ""):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    return text[start:i+1]
    return text


def _chat_once(model: str, messages: list, fmt=None):
    kwargs = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "seed": 42},
    }
    if fmt is not None:
        kwargs["format"] = fmt
    return chat(**kwargs)


if __name__ == "__main__":
    # Prefer CLI arg for image path; fall back to sample
    img_path = sys.argv[1] if len(sys.argv) > 1 else "./few_shot_sample/image/8_triple_receipt.jpg"
    b64 = img_to_b64(img_path)

    system_msg = (
        "You are a document understanding assistant. "
        "Classify the document and extract fields. Return only valid JSON matching the provided schema. "
        "Use null for any field you cannot find; do not fabricate values. "
        "Return one JSON object strictly matching this JSON schema: "
        + json.dumps(GENERATION_SCHEMA, ensure_ascii=False)
    )

    user_msg = (
        "Task: 1) Choose doc_class from {business_invoice, customs_tax_payment, receipt, id_card, other}. "
        "2) Extract header/tail fields where applicable. "
        "3) Provide a confidence in [0,1]. "
        "If unsure about a value, set it to null."
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg, "images": [b64]},
    ]

    content = None
    errors = []

    # 1) Try preferred model with JSON mode
    try:
        resp = _chat_once('qwen2.5vl:7b', messages, fmt="json")
        content = resp.message.content
        print(resp.message.content)
    except Exception as e:
        errors.append(f"7b json mode: {e}")
        # 2) Retry same model without format (some servers/models choke on format)
        try:
            resp = _chat_once('qwen2.5vl:7b', messages, fmt=None)
            content = _extract_first_json_block(resp.message.content)
        except Exception as e2:
            errors.append(f"7b raw: {e2}")


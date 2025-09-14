#!/usr/bin/env python3
from __future__ import annotations
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel
from ollama import chat
import sys
import json

# ====== JSON Schema（Pydantic）======
DocClass = Literal[
    'business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',
    'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other'
]

class Doc(BaseModel):
    doc_class: DocClass
    header: Optional[Dict[str, Optional[str]]] = None
    body:   Optional[Dict[str, Optional[str]]] = None
    tail:   Optional[Dict[str, Optional[str]]] = None
    rationale: Optional[str] = None

# ====== 工具：回退解析器（模型若夾雜文字時擷取首段 JSON）======
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

# ====== 單張圖片推論 ======
def infer_image_json(
    img_path: str,
    model: str = 'invoice-cls',   # 使用你剛 create 的本地模型名
) -> str:
    user_prompt = (
        "請分類這張文件並輸出單一 JSON："
        "1) 給出 doc_class（九類其一）；"
        "2) 依 header/body/tail 結構輸出欄位；未知請為 null 或省略；"
        "3) 可附上 rationale（可省略）；只輸出 JSON，勿加解說。"
    )

    messages = [
        {
            "role": "user",
            "content": user_prompt,
            # 直接傳圖片路徑；也可改成 base64 串列
            "images": [img_path],
        }
    ]

    # 優先：Structured Outputs（最穩）
    try:
        resp = chat(
            model=model,
            messages=messages,
            stream=False,
            options={"temperature": 0, "seed": 42},
            format=Doc.model_json_schema(),   # 關鍵：強制符合 Schema
        )
        return resp.message.content
    except Exception:
        # 後備：無 format，再從文字中抽 JSON
        resp = chat(
            model=model,
            messages=messages,
            stream=False,
            options={"temperature": 0, "seed": 42},
        )
        return _extract_first_json_block(resp.message.content)

# ====== CLI ======
if __name__ == "__main__":
    img_path = sys.argv[1] if len(sys.argv) > 1 else "./invoice2.jpg"
    out = infer_image_json(img_path)
    # 若你想驗證 Schema，可反序列化看看
    try:
        parsed = Doc.model_validate_json(out)
        print(parsed.model_dump_json(ensure_ascii=False, indent=2))
    except Exception:
        # 仍印出原始（多半已是 JSON 字串）
        try:
            obj = json.loads(out)
            print(json.dumps(obj, ensure_ascii=False, indent=2))
        except Exception:
            print(out)

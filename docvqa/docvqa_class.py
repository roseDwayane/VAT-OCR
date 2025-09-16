from ollama import chat
from pydantic import ValidationError
from typing import Literal, Optional
from pathlib import Path

labels = [
    {"name":"business_invoice", "definition":"header is 電子發票證明聯，具有表格的發票，包含統編、發票字軌與品項總計"},
    {"name":"customs_tax_payment", "definition":"關稅/稅單；包含海關或課稅字樣與稅額"},
    {"name":"receipt2", "definition":"header is 收銀機統一發票"},
    {"name":"id_card", "definition":"身分證或帶大頭照的證件"},
    {"name":"other", "definition":"以上皆非"}
]

system_rules = f"""你是嚴格的影像文件分類器。僅能在下列標籤中選一個：
{[l["name"] for l in labels]}
判斷原則：依各標籤定義，不確定時選 other。回傳 JSON、且僅能是 JSON。"""

img = "./few_shot_sample/image/1_business_invoice.jpg"  # ← 改成你的檔案

from pydantic import BaseModel
class DocClass(BaseModel):
    label: Literal['business_invoice','customs_tax_payment','receipt','id_card','other']
    confidence: float
    rationale: Optional[str]

resp = chat(
    model='qwen2.5vl:7b',
    messages=[
        {'role':'system','content':system_rules},
        {'role':'user',
         'content':"請以單選分類這張圖片，並解釋你依據的線索。",
         'images':[img]},  # 路徑可直接放入（新版支援），或改用 base64
    ],
    format=DocClass.model_json_schema(),   # ★ 強制 JSON Schema
    options={'temperature':0, 'seed':42},  # 穩定輸出
)

print(resp.message.content)  # 嚴格的 JSON，符合 DocClass

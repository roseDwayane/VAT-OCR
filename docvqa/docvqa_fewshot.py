from typing import Literal, Optional
from pydantic import BaseModel
from ollama import chat
import base64


def img_to_b64(path: str) -> str:
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


class DocClass(BaseModel):
    label: Literal[
        'business_invoice', 'customs_tax_payment', 'e_invoice',
        'plumb_payment_order', 'tele_payment_order', 'tradition_invoice',
        'triple_invoice', 'triple_receipt', 'other'
    ]
    confidence: float
    rationale: Optional[str]


system_rules = (
    "你是發票/單據分類器。請輸出嚴格符合 JSON Schema 的 JSON。"
    "在 ['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',"
    "'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other'] 之中選擇 label。"
)


# Few-shot examples using repository images
ex1_img_path = './few_shot_sample/image/1_business_invoice.jpg'
ex2_img_path = './few_shot_sample/image/8_triple_receipt.jpg'

shots = [
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex1_img_path)],
    },
    {
        'role': 'assistant',
        'content': '{"label":"business_invoice","confidence":0.92,"rationale":"電子發票證明聯，含發票字樣、發票號碼、銷售額與稅額匯總"}',
    },
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex2_img_path)],
    },
    {
        'role': 'assistant',
        'content': '{"label":"triple_receipt","confidence":0.95,"rationale":"收銀機統一發票，三聯收據格式，含統編與金額欄位"}',
    },
]


# Test image (you can change this path)
test_img_path = './invoice.jpg'

resp = chat(
    model='qwen2.5vl:7b',
    messages=[
        {'role': 'system', 'content': system_rules},
        *shots,
        {'role': 'user', 'content': '請分類這張待測文件', 'images': [img_to_b64(test_img_path)]},
    ],
    format=DocClass.model_json_schema(),
    options={'temperature': 0, 'seed': 7},
)

print(resp.message.content)


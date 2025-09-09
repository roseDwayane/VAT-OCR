from typing import Literal, Optional
from pydantic import BaseModel
from ollama import chat
import base64


def img_to_b64(path: str) -> str:
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

class Header(BaseModel):
    PrefixTwoLetters: Optional[str] = None
    InvoiceNumber: Optional[str] = None
    #-----------
    CompanyName: Optional[str] = None
    InvoiceYear: Optional[str] = None
    InvoiceMonth: Optional[str] = None
    InvoiceDay: Optional[str] = None
    BuyerTaxIDNumber: Optional[str] = None


class Body(BaseModel):
    CompanyName: Optional[str] = None
    PhoneNumber: Optional[str] = None
    CompanyTaxIDNumber: Optional[str] = None
    CompanyAddress: Optional[str] = None
    InvoiceYear: Optional[str] = None
    InvoiceMonth: Optional[str] = None
    InvoiceDay: Optional[str] = None
    BuyerTaxIDNumber: Optional[str] = None
    BuyerName: Optional[str] = None
    Abstract: Optional[str] = None

class Tail(BaseModel):
    SalesTotalAmount: Optional[str] = None
    SalesTax: Optional[str] = None
    TotalAmount: Optional[str] = None
    #-----------
    CompanyTaxIDNumber: Optional[str] = None

class DocClass(BaseModel):
    doc_class: Literal[
        'business_invoice', 'customs_tax_payment', 'e_invoice',
        'plumb_payment_order', 'tele_payment_order', 'tradition_invoice',
        'triple_invoice', 'triple_receipt', 'other'
    ]
    rationale: Optional[str]
    header: Header | None = None
    body: Body | None = None
    tail: Tail | None = None
    notes: Optional[str] = None


system_rules = (
    "你是發票/單據分類器。請輸出嚴格符合 JSON Schema 的 JSON。"
    "在 ['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',"
    "'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other'] 之中選擇 label。"
)

business_invoice = """{
    "doc_class": "business_invoice",
    "rationale":"電子發票證明聯，包含日期、發票號碼、買方、統一編號、品名、數量、單價、金額、備註、銷售額合計、營業稅、總計、營業人蓋統一發票專用章(賣方、統一編號、地址)"
    "header": {
        "CompanyName": "慶陽事務用品有限公司",
        "InvoiceYear": "2021",
        "InvoiceMonth": "09",
        "InvoiceDay": "30",
        "PrefixTwoLetters": "SX",
        "InvoiceNumber": "58421758",
        "BuyerTaxIDNumber": "53812386"
    },
    "body": {
        "Abstract": "雲彩紙 312 14.00 4,368\n 美術紙 359 30.00 10,770\n 灰紙板 333 15.00 4,995\n 工業用板 1,000 25.00 25,000"
    },
    "tail": {
        "SalesTotalAmount": "45133",
        "SalesTax": "2257",
        "TotalAmount": "47390",
        "CompanyTaxIDNumber": "23944895",

    }
}
"""

triple_receipt = """{
    "doc_class": "triple_receipt",
    "rationale":"收銀機統一發票，包含發票號碼、日期、統編、買受人、銷售額、營業稅、總計",
    "header": {
        "PrefixTwoLetters": "RH",
        "InvoiceNumber": "15255935"
    },
    "body": {
        "CompanyName": "九達生活禮品股份有限公司",
        "PhoneNumber": "06-2702917",
        "CompanyTaxIDNumber": "#16900386",
        "CompanyAddress": "台南市歸仁區許厝里公園路152號1樓",
        "InvoiceYear": "110",
        "InvoiceMonth": "9",
        "InvoiceDay": "17",
        "BuyerTaxIDNumber": "53812386",
        "BuyerName": "彩琿實業有限公司",
        "Abstract": "喵咪刺繡皮標上翻筆貸 105個 119.73 12,572"
    },
    "tail": {
        "SalesTotalAmount": "12572",
        "SalesTax": "629",
        "TotalAmount": "13201"
    }
}
"""

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
        'content': business_invoice,
    },
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex2_img_path)],
    },
    {
        'role': 'assistant',
        'content': triple_receipt,
    },
]


# Test image (you can change this path)
test_img_path = './invoice2.jpg' #'./few_shot_sample/image/1_business_invoice.jpg', './invoice2.jpg'

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


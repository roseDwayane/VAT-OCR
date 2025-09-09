from typing import Literal, Optional
from pydantic import BaseModel
from ollama import chat
import base64
import sys
import json


def img_to_b64(path: str) -> str:
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')



system_rules = (
    "你是發票/單據分類器。請輸出嚴格符合 JSON Schema 的 JSON。"
    "在 ['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',"
    "'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other'] 之中選擇 label。"
)

business_invoice = """{
    "doc_class": "business_invoice",
    "rationale":"電子發票證明聯，包含日期、發票號碼、買方、統一編號、品名、數量、單價、金額、備註、銷售額合計、營業稅、總計、營業人蓋統一發票專用章(賣方、統一編號、地址)",
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
        "CompanyTaxIDNumber": "23944895"

    }
}
"""

customs_tax_payment = """{
    "doc_class": "customs_tax_payment",
    "rationale":"海關進口快遞貨物稅費繳納證明，包含稅單號碼、統一編號、納稅義務人、營業稅、營業稅稅基",
    "header": {
        "PrefixThreeLetters": "CXI",
        "TaxBillNumber": "21180EFF197",
        "CompanyTaxIDNumber": "12698538",
        "CompanyName": 明緯貿易有限公司
    },
    "body": {
        "InvoiceYear": "108",
        "InvoiceMonth": "06",
        "InvoiceDay": "05",
        "Abstract": "海關進口"
    },
    "tail": {
        "SalesTax": "176",
        "TotalAmount": "3536"
    }
}
"""

e_invoice = """{
    "doc_class": "e_invoice",
    "rationale":"電子發票證明聯，包含日期、發票號碼、隨機碼、總計、賣方、買方",
    "header": {
        "PrefixTwoLetters": "RC",
        "InvoiceNumber": "82802197"
    },
    "body": {
        "InvoiceYear": "2021",
        "InvoiceMonth": "07",
        "InvoiceDay": "29",
        "TotalAmount": "80"
        "CompanyTaxIDNumber": "99636932",
        "BuyerTaxIDNumber": "53812386",
        "Abstract": "電子發票證明聯"
    },
    "tail": {
        "SalesTotalAmount": "76",
        "SalesTax": "4",
        "TotalAmount": "80"
    }
}
"""

plumb_payment_order = """{
    "doc_class": "plumb_payment_order",
    "rationale":"台灣自來水股份有限公司水費通知單",
    "header": {
        "BuyerAddress": "台北市松山區復興南路1段1號12樓之1",
        "BuyerName": "彩琿實業有限公司"
    },
    "body": {
        "PrefixFourLetters": "BBMS",
        "SerialNumber": "002060",
        "BuyerTaxIDNumber": "53812386",
        "CompanyTaxIDNumber": "00904745"
    },
    "tail": {
        "TotalAmount": "212"
    }
}
"""

tele_payment_order = """{
    "doc_class": "tele_payment_order",
    "rationale":"電信股份有限公司",
    "header": {
        "BuyerAddress": "台北市松山區復興南路1段1號12樓之1",
        "BuyerName": "彩琿實業有限公司",
        "PrefixTwoLetters": "BB",
        "SerialNumber": "42518759",
        "CompanyTaxIDNumber": "52003801",
        "TotalAmount": "1229"
    },
    "body": {
        "BuyerTaxIDNumber": "53812386",
        "Abstract": "4G行動電話1399型月租費 1322\n 4G來電答鈴月租費 29\n 4G行動月租費優惠 -191"
    },
    "tail": {
        "GeneralTaxRate": "1170",
        "ZeroTax": "0",
        "DutyFree": "0",
        "OtherFee": "0",
        "SalesTax": "59",
        "TotalAmount": "1229"
    }
}
"""

tradition_invoice = """{
    "doc_class": "tradition_invoice",
    "rationale":"收銀機統一發票(收執聯)",
    "header": {
        "PrefixTwoLetters": "FY",
        "InvoiceNumber": "03779651"
    },
    "body": {
        "CompanyTaxIDNumber": "66266727",
        "PhoneNumber": "(02)2392-4578",
        "InvoiceYear": "2024",
        "InvoiceMonth": "12",
        "InvoiceDay": "06",
        "Abstract": "麵包"
    },
    "tail": {
        "TotalAmount": "195"
    }
}
"""

triple_invoice = """{
    "doc_class": "triple_invoice",
    "rationale":"統一發票(三聯式)",
    "header": {
        "PrefixTwoLetters": "KY",
        "InvoiceNumber": "54957806",
        "BuyerName": "建邦貿易有限公司",
        "BuyerTaxIDNumber": "12361788",
        "InvoiceYear": "112",
        "InvoiceMonth": "3",
        "InvoiceDay": "6"
    },
    "body": {
        "Abstract": "零件2批 25780"
    },
    "tail": {
        "SalesTotalAmount": "25780",
        "SalesTax": "1289",
        "TotalAmount": "27069",
        "CompanyName": "金暉汽材有限公司",
        "CompanyTaxIDNumber": "12868673",
        "PhoneNumber": "02-2599-5123",
        "CompanyAddress": "台北市中山區新生北路3段93巷18號"
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
ex2_img_path = './few_shot_sample/image/2_customs_tax_payment.jpg'
ex3_img_path = './few_shot_sample/image/3_e_invoice.jpg'
ex4_img_path = './few_shot_sample/image/4_plumb_payment_order.jpg'
ex5_img_path = './few_shot_sample/image/5_tele_payment_order.jpg'
ex6_img_path = './few_shot_sample/image/6_tradition_invoice.jpg'
ex7_img_path = './few_shot_sample/image/7_triple_invoice.jpg'
ex8_img_path = './few_shot_sample/image/8_triple_receipt.jpg'

shots = [
    # 1.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex1_img_path)],
    },
    {
        'role': 'assistant',
        'content': business_invoice,
    },
    # 2.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex2_img_path)],
    },
    {
        'role': 'assistant',
        'content': customs_tax_payment,
    },
    # 3.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex3_img_path)],
    },
    {
        'role': 'assistant',
        'content': e_invoice,
    },
    # 4.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex4_img_path)],
    },
    {
        'role': 'assistant',
        'content': plumb_payment_order,
    },
    # 5.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex5_img_path)],
    },
    {
        'role': 'assistant',
        'content': tele_payment_order,
    },
    # 6.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex6_img_path)],
    },
    {
        'role': 'assistant',
        'content': tradition_invoice,
    },
    # 7.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex7_img_path)],
    },
    {
        'role': 'assistant',
        'content': triple_invoice,
    },
    # 8.
    {
        'role': 'user',
        'content': '請分類這張文件',
        'images': [img_to_b64(ex8_img_path)],
    },
    {
        'role': 'assistant',
        'content': triple_receipt,
    },
]



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
    test_img_path = './few_shot_sample/image/3_e_invoice.jpg' #'./few_shot_sample/image/1_business_invoice.jpg', './invoice2.jpg'
    img_path = sys.argv[1] if len(sys.argv) > 1 else test_img_path
    b64 = img_to_b64(img_path)

    system_msg = (
        "You are a document understanding assistant. "
        "Classify the document into one of: "
        "['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',"
        "'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other']. "
        "Then extract fields into JSON with keys: doc_class, header, body, tail, rationale (optional). "
        "Amounts must be digits only (no commas). If unknown, use null or omit the property. "
        "Return JSON only, no extra text."
    )

    user_msg = (
        "請分析這張文件並輸出單一 JSON。"
        "1) 選擇 doc_class（上列九類其一）。"
        "2) 擷取 header/body/tail 相關欄位；不確定的設為 null 或省略。"
        "3) 給出合理的 rationale（可省略）。"
        "只輸出 JSON，勿加解說。"
    )

    messages = [
        {"role": "system", "content": system_msg},
        *shots,
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


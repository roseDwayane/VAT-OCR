# save as qwen_test.py
import base64, requests, sys, json, time

img_path = sys.argv[1]          # e.g. .\samples\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Unified Invoice/Receipt Schema (TW, 8 classes)",
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "class": {
      "type": "string",
      "enum": [
        "business_invoice",
        "customs_tax_payment",
        "e_invoice",
        "plumb_payment_order",
        "tele_payment_order",
        "tradition_invoice",
        "triple_invoice",
        "triple_receipt"
      ]
    },
    "header": { "type": "object" },
    "body": { "type": "object" },
    "tail": { "type": "object" },
    "all": { "type": "object" },
    "other": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["class"],
  "oneOf": [
    {
      "title": "1) business_invoice",
      "properties": {
        "class": { "const": "business_invoice" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["InvoiceYear", "InvoiceMonth", "InvoiceDay", "PrefixTwoLetters", "InvoiceNumber", "BuyerTaxIDNumber"],
          "properties": {
            "InvoiceYear": { "type": "string", "pattern": "^\\d{2,4}$" },
            "InvoiceMonth": { "type": "string", "pattern": "^\\d{1,2}$" },
            "InvoiceDay": { "type": "string", "pattern": "^\\d{1,2}$" },
            "PrefixTwoLetters": { "type": "string", "pattern": "^[A-Z]{2}$" },
            "InvoiceNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "BuyerTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" }
          }
        },
        "body": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["SalesTotalAmount", "SalesTax", "TotalAmount"],
          "properties": {
            "SalesTotalAmount": { "type": "string", "pattern": "^\\d+$" },
            "SalesTax": { "type": "string", "pattern": "^\\d+$" },
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "body", "tail", "other"]
    },
    {
      "title": "2) customs_tax_payment",
      "properties": {
        "class": { "const": "customs_tax_payment" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber", "PrefixThreeLetters", "TaxBillNumber"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "PrefixThreeLetters": { "type": "string", "pattern": "^[A-Z]{3}$" },
            "TaxBillNumber": { "type": "string", "pattern": "^[A-Z0-9]+$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["SalesTax", "TotalAmount"],
          "properties": {
            "SalesTax": { "type": "string", "pattern": "^\\d+$" },
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "tail", "other"]
    },
    {
      "title": "3) e_invoice",
      "properties": {
        "class": { "const": "e_invoice" },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class"]
    },
    {
      "title": "4) plumb_payment_order",
      "properties": {
        "class": { "const": "plumb_payment_order" },
        "all": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber", "TotalAmount", "PrefixFourLetters", "SerialNumber"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" },
            "PrefixFourLetters": { "type": "string", "pattern": "^[A-Z]{4}$" },
            "SerialNumber": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "all", "other"]
    },
    {
      "title": "5) tele_payment_order",
      "properties": {
        "class": { "const": "tele_payment_order" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["PrefixTwoLetters", "SerialNumber", "CompanyTaxIDNumber", "TotalAmount"],
          "properties": {
            "PrefixTwoLetters": { "type": "string", "pattern": "^[A-Z]{2}$" },
            "SerialNumber": { "type": "string", "pattern": "^\\d+$" },
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["GeneralTaxRate", "ZeroTax", "DutyFree", "OtherFee", "SalesTax"],
          "properties": {
            "GeneralTaxRate": { "type": "string", "pattern": "^\\d+$" },
            "ZeroTax": { "type": "string", "pattern": "^\\d+$" },
            "DutyFree": { "type": "string", "pattern": "^\\d+$" },
            "OtherFee": { "type": "string", "pattern": "^\\d+$" },
            "SalesTax": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "tail", "other"]
    },
    {
      "title": "6) tradition_invoice",
      "properties": {
        "class": { "const": "tradition_invoice" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["PrefixTwoLetters", "InvoiceNumber"],
          "properties": {
            "PrefixTwoLetters": { "type": "string", "pattern": "^[A-Z]{2}$" },
            "InvoiceNumber": { "type": "string", "pattern": "^\\d{8}$" }
          }
        },
        "body": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber", "InvoiceYear", "InvoiceMonth", "InvoiceDay"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "InvoiceYear": { "type": "string", "pattern": "^\\d{2,4}$" },
            "InvoiceMonth": { "type": "string", "pattern": "^\\d{1,2}$" },
            "InvoiceDay": { "type": "string", "pattern": "^\\d{1,2}$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["TotalAmount"],
          "properties": {
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "body", "tail", "other"]
    },
    {
      "title": "7) triple_invoice",
      "properties": {
        "class": { "const": "triple_invoice" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["InvoiceNumber", "PrefixTwoLetters"],
          "properties": {
            "InvoiceNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "PrefixTwoLetters": { "type": "string", "pattern": "^[A-Z]{2}$" }
          }
        },
        "body": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber", "InvoiceDay", "InvoiceMonth", "InvoiceYear"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" },
            "InvoiceDay": { "type": "string", "pattern": "^\\d{1,2}$" },
            "InvoiceMonth": { "type": "string", "pattern": "^\\d{1,2}$" },
            "InvoiceYear": { "type": "string", "pattern": "^\\d{2,4}$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["SalesTotalAmount", "SalesTax"],
          "properties": {
            "SalesTotalAmount": { "type": "string", "pattern": "^\\d+$" },
            "SalesTax": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "body", "tail", "other"]
    },
    {
      "title": "8) triple_receipt",
      "properties": {
        "class": { "const": "triple_receipt" },
        "header": {
          "type": "object",
          "additionalProperties": False,
          "required": ["PrefixTwoLetters", "InvoiceNumber"],
          "properties": {
            "PrefixTwoLetters": { "type": "string", "pattern": "^[A-Z]{2}$" },
            "InvoiceNumber": { "type": "string", "pattern": "^\\d{8}$" }
          }
        },
        "body": {
          "type": "object",
          "additionalProperties": False,
          "required": ["CompanyTaxIDNumber", "InvoiceYear", "InvoiceMonth", "InvoiceDay", "PhoneNumber", "BuyerTaxIDNumber"],
          "properties": {
            "CompanyTaxIDNumber": { "type": "string", "pattern": "^#?\\d{8}$" },
            "InvoiceYear": { "type": "string", "pattern": "^\\d{2,4}$" },
            "InvoiceMonth": { "type": "string", "pattern": "^\\d{1,2}$" },
            "InvoiceDay": { "type": "string", "pattern": "^\\d{1,2}$" },
            "PhoneNumber": { "type": "string", "pattern": "^[0-9\\-()+]{6,20}$" },
            "BuyerTaxIDNumber": { "type": "string", "pattern": "^\\d{8}$" }
          }
        },
        "tail": {
          "type": "object",
          "additionalProperties": False,
          "required": ["SalesTotalAmount", "SalesTax", "TotalAmount"],
          "properties": {
            "SalesTotalAmount": { "type": "string", "pattern": "^\\d+$" },
            "SalesTax": { "type": "string", "pattern": "^\\d+$" },
            "TotalAmount": { "type": "string", "pattern": "^\\d+$" }
          }
        },
        "other": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["class", "header", "body", "tail", "other"]
    }
  ]
}


payload = {
  "model": "qwen2.5vl:7b",   # 若顯存吃緊換成 qwen2.5vl:3b
  "stream": False,
  "format": "json",
  "options": {"temperature":0},
  "messages": [
    {"role": "system", "content": "You are a document QA assistant. Return only one JSON object: {'class':'triple_invoice','header':{'PrefixTwoLetters':string,'InvoiceNumber':string},'body':{'InvoiceDay':string,'InvoiceMonth':string,'InvoiceYear':string,'CompanyTaxIDNumber':string},'tail':{'SalesTotalAmount':string,'SalesTax':string},'other':string}. No extra keys or text. Use 'unknown' for any missing field."},
    {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64]},
    {"role": "user", "content": question}
  ]
}
start_time = time.time()
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)

# Robust response handling
try:
    data = r.json()
except Exception:
    print("Non-JSON response from server:")
    print(r.text)
    print("running time: ", time.time()-start_time)
    sys.exit(1)

if not r.ok:
    print(f"HTTP {r.status_code} error from API")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("running time: ", time.time()-start_time)
    sys.exit(1)

content = None
if isinstance(data, dict):
    if isinstance(data.get("message"), dict):
        content = data["message"].get("content")
    if content is None:
        content = data.get("content") or data.get("response")

if isinstance(content, str):
    print(content.strip())
else:
    print(json.dumps(data, ensure_ascii=False, indent=2))
print("running time: ", time.time()-start_time)

# python .\qwen_test.py .\invoice.jpg 
# "請給我整張圖片完整的資訊"
# "請問這張圖片中的銷售額、營業稅、總計分別是多少"
# "請問這張圖片中的 1. 發票字軌(兩個英文字母) 2. 發票號碼 3. 統編 4. 日期 5. 買受人 6. 銷售額 7. 營業稅 8. 總計，並輸出每一項的信心分數"

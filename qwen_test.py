# save as qwen_test.py
import base64, requests, sys, json, time

img_path = sys.argv[1]          # e.g. .\samples\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

# ---- Custom JSON Schema for structured output ----
# Target instance example:
# {'class': 'customs_tax_payment', 'header': {'CompanyTaxIDNumber': '12698538', 'PrefixThreeLetters': 'CAI', 'TaxBillNumber': '31180475237'}, 'tail': {'TotalAmount': '26734', 'SalesTax': '1336'}}
CUSTOMS_TAX_PAYMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "class": {"const": "customs_tax_payment"},
        "header": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "CompanyTaxIDNumber": {"type": "string", "pattern": "^[0-9]{8,}$"},
                "PrefixThreeLetters": {"type": "string", "pattern": "^[A-Z]{3}$"},
                "TaxBillNumber": {"type": "string", "pattern": "^[0-9]+$"}
            },
            "required": [
                "CompanyTaxIDNumber",
                "PrefixThreeLetters",
                "TaxBillNumber"
            ]
        },
        "tail": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "TotalAmount": {"type": "string", "pattern": "^[0-9]+$"},
                "SalesTax": {"type": "string", "pattern": "^[0-9]+$"}
            },
            "required": [
                "TotalAmount",
                "SalesTax"
            ]
        }
    },
    "required": ["class", "header", "tail"]
}

# Toggle: if True, attempt to send the JSON Schema via payload['format'].
# Note: Some Ollama versions only accept the string "json" for 'format'.
# If you see a 400 error, set this to False to fall back to "json" and rely on prompting.
USE_FORMAT_SCHEMA = True

format_field = (
    {
        # Some providers expect a wrapper like {"type":"json_schema","json_schema":{...}}.
        # If you hit an error when calling the API, set USE_FORMAT_SCHEMA = False.
        "type": "json_schema",
        "json_schema": {
            "name": "customs_tax_payment",
            "schema": CUSTOMS_TAX_PAYMENT_SCHEMA
        }
    } if USE_FORMAT_SCHEMA else "json"
)

payload = {
  "model": "qwen2.5vl:7b",   # 若顯存吃緊換成 qwen2.5vl:3b
  "stream": False,
  "format": format_field,
  "options": {"temperature":0},
  "messages": [
    {"role": "system", "content": "You are a document QA assistant. Return only one JSON object: {'class':'customs_tax_payment','header':{'CompanyTaxIDNumber':string,'PrefixThreeLetters':string,'TaxBillNumber':string},'tail':{'TotalAmount':string,'SalesTax':string}}. No extra keys or text. Use 'unknown' for any missing field."},
    {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64]},
    {"role": "user", "content": question}
  ]
}
start_time = time.time()
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
print(json.loads(r.text)["message"]["content"].strip())
print("running time: ", time.time()-start_time)

# python .\qwen_test.py .\invoice.jpg 
# "請給我整張圖片完整的資訊"
# "請問這張圖片中的銷售額、營業稅、總計分別是多少"
# "請問這張圖片中的 1. 發票字軌(兩個英文字母) 2. 發票號碼 3. 統編 4. 日期 5. 買受人 6. 銷售額 7. 營業稅 8. 總計，並輸出每一項的信心分數"

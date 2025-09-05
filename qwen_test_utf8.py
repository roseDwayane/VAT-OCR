# save as qwen_test.py
import base64, requests, sys, json, time

img_path = sys.argv[1]          # e.g. .\samples\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

schema = {
  "type": "object",
  "minProperties": 1, "maxProperties": 1,
  "additionalProperties": False,
  "patternProperties": {
    "^.+$": {  # ???憭惜?蛛??虜?舀???URL嚗?
      "type": "object",
      "additionalProperties": False,
      "required": ["filename", "size", "regions"],
      "properties": {
        "filename": {"type": "string"},
        "size": {"type": "string"},
        "regions": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["shape_attributes", "region_attributes"],
            "properties": {
              "shape_attributes": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "x", "y", "width", "height"],
                "properties": {
                  "name": {"const": "rect"},
                  "x": {"type": "integer"}, "y": {"type": "integer"},
                  "width": {"type": "integer"}, "height": {"type": "integer"}
                }
              },
              "region_attributes": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "value"],
                "properties": {
                  "name": {"type": "string"},
                  "value": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}

payload = {
  "model": "qwen2.5vl:7b",   # ?仿＊摮?蝺???qwen2.5vl:3b
  "stream": False,
  "format": schema,
  "options": {"temperature":0},
  "messages": [
    {"role": "system", "content": "You are a document QA assistant. Return only one JSON object: {'class':'customs_tax_payment','header':{'CompanyTaxIDNumber':string,'PrefixThreeLetters':string,'TaxBillNumber':string},'tail':{'TotalAmount':string,'SalesTax':string}}. No extra keys or text. Use 'unknown' for any missing field."},
    {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64]},
    {"role": "user", "content": question}
  ]
}
start_time = time.time()
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
print(r.text)
print(json.loads(r.text)["message"]["content"].strip())
print("running time: ", time.time()-start_time)

# python .\qwen_test.py .\invoice.jpg 
# "隢策?撘萄????渡?鞈?"
# "隢??撐??銝剔??瑕憿?璆剔??蜇閮??交憭?"
# "隢??撐??銝剔? 1. ?潛巨摮?(?拙??瘥? 2. ?潛巨?Ⅳ 3. 蝯梁楊 4. ?交? 5. 鞎瑕?鈭?6. ?瑕憿?7. ?平蝔?8. 蝮質?嚗蒂頛詨瘥???靽∪??"

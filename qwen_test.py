# save as test_docvqa.py
import base64, requests, sys, json

img_path = sys.argv[1]          # e.g. .\samples\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
  "model": "qwen2.5vl:7b",   # 若顯存吃緊換成 qwen2.5vl:3b
  "stream": False,
  "messages": [
    {"role": "system", "content": "You are a document QA assistant. Reply with the exact text span from the document only."},
    {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64]},
    {"role": "user", "content": question}
  ]
}
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
print(json.loads(r.text)["message"]["content"].strip())

# python .\qwen_test.py .\invoice.jpg "請給我發票號碼、"
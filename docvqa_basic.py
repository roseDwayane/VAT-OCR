# save as qwen_test.py
import base64, requests, sys, json, time

img_path = sys.argv[1]          # e.g. .\samples\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')


payload = {
  "model": "qwen2.5vl:7b",   # llama3.2-vision, qwen2.5vl:7b
  "stream": False,
  #"format": "json",
  "options": {"temperature":0},
  "messages": [
    {"role":"system","content":"You are a document QA assistant. Reply with the exact text span from the document only."},
    {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64]},
    {"role": "user", "content": question}
  ]
}
start_time = time.time()
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
print(r.text)
print(json.loads(r.text)["message"]["content"].strip())
print(r)
print("running time: ", time.time()-start_time)

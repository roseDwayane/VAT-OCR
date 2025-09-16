# save as qwen_test.py
import base64, requests, sys, json, time

img_path = sys.argv[1]          # e.g. .\invoice.jpg
question = sys.argv[2]          # e.g. "What is the invoice number?"

with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')


payload = {
  "model": "my-qwen25vl",   # llama3.2-vision, qwen2.5vl:7b, gemma3:12b, invoice-cls, my-qwen25vl
  "stream": False,
  #"format": "json",
  "options": {"temperature":0.2, "repeat_penalty": 1.1},
  "messages": [
    {"role":"system","content":"You are a document QA assistant. Reply with the exact text span from the document only."},
    {"role": "user", "content": question, "images": [b64]},#[b64]
    #{"role": "user", "content": question}
    #{"role":"system","content":"You are an eye-tracking image analyst. Answer only based on visible information in the image. Do not infer the participant's age, mood, or performance score. Please divide your answer into two sections: * Observations (only visible facts: paths, hot spots, area of ​​interest, etc.) * Inferences (possible tasks and meanings, with a high/medium/low confidence rating). Use English. List the key points and avoid verbose text."},
    #{"role": "user", "content": "Please read this eye movement diagram and list the **observations** first, then the **inferences**.", "images": [b64]},#[b64]
    #{"role": "user", "content": question}
    
  ]
}
start_time = time.time()
r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
print(r.text)
print(json.loads(r.text)["message"]["content"].strip())
print(r)
print("running time: ", time.time()-start_time)

# "你是發票/單據分類器與結構化抽取器，請辨識這張文件"
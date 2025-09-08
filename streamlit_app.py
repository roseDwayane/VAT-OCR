# qwen_streamlit_app.py
# Streamlit app to query Ollama Qwen2.5-VL with an uploaded image and a question

import streamlit as st
import base64
import requests
import time
import json

st.set_page_config(page_title="DocVQA - 文件問答", page_icon="🧾")

st.title("🧾 Qwen2.5‑VL 文件問答（Ollama）")
st.caption("上傳一張票據/文件影像 + 問一個問題 → 以**原文片段**作答；若找不到回覆 `unknown`。")

with st.sidebar:
    st.header("連線設定")
    server_url = st.text_input(
        "Ollama 伺服器 API 位址",
        value="http://localhost:11434/api/chat",
        help="預設為本機 11434 連到 /api/chat。若您遠端執行 Ollama，請改成對應位址。"
    )
    model = st.text_input(
        "模型名稱",
        value="qwen2.5vl:7b",
        help="若顯存不足可改為 qwen2.5vl:3b（請先在終端機執行：`ollama pull qwen2.5vl:3b`）。"
    )
    temperature = st.slider("temperature", 0.0, 1.0, 0.0, 0.1)
    timeout_s = st.number_input("請求逾時（秒）", min_value=10, max_value=600, value=120, step=10)
    st.markdown("---")
    st.markdown("**小提示**：請先確保已在終端機執行 `ollama run qwen2.5vl:7b` 或 `ollama pull qwen2.5vl:7b` 下載模型。")

st.subheader("步驟 1：上傳影像")
uploaded = st.file_uploader("支援 jpg / jpeg / png / webp / bmp / tiff / gif（圖片越清晰越好）",
                            type=["jpg","jpeg","png","webp","bmp","tiff","gif"])

# === 影像預覽：上傳後即顯示在頁面 ===
file_bytes = None
if uploaded is not None:
    file_bytes = uploaded.getvalue()
    size_kb = len(file_bytes) / 1024
    with st.expander("📷 影像預覽（點此展開/收合）", expanded=True):
        st.image(file_bytes, caption=f"已上傳：{uploaded.name}（{size_kb:.1f} KB）", use_column_width=True)

st.subheader("步驟 2：輸入問題")
question = st.text_input("範例：What is the invoice number? （英文更準確）", value="")

go = st.button("🚀 送出查詢")

def encode_image_to_b64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")

def ask_ollama(server_url: str, model: str, b64_image: str, question: str, temperature: float, timeout_s: int):
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": float(temperature)},
        "messages": [
            {"role": "system", "content": "You are a document QA assistant. Reply with the exact text span from the document only."},
            {"role": "user", "content": "If not found, reply `unknown`.", "images": [b64_image]},
            {"role": "user", "content": question}
        ]
    }
    start_time = time.time()
    try:
        r = requests.post(server_url, json=payload, timeout=timeout_s)
    except requests.exceptions.RequestException as e:
        return {"error": f"連線錯誤：{e}"}, 0.0

    elapsed = time.time() - start_time

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text}"}, elapsed

    try:
        data = r.json()
    except json.JSONDecodeError:
        return {"error": f"無法解析回應：{r.text[:500]}..."}, elapsed

    return data, elapsed

if go:
    if uploaded is None:
        st.warning("請先上傳一張影像。")
    elif not question.strip():
        st.warning("請輸入問題。")
    else:
        b64 = encode_image_to_b64(uploaded.getvalue())
        with st.spinner("模型推理中，請稍候…"):
            data, elapsed = ask_ollama(server_url, model, b64, question.strip(), temperature, int(timeout_s))

        if "error" in data:
            st.error(data["error"])
        else:
            answer = (data.get("message") or {}).get("content", "").strip()
            st.success(f"回答：{answer}")
            st.caption(f"執行時間：{elapsed:.2f} 秒")

            with st.expander("檢視原始回應 JSON"):
                st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")



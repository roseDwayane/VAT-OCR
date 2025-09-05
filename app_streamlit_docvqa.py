import base64, json, io, os, requests, statistics
from typing import List, Dict, Any
from PIL import Image
import streamlit as st
from rapidfuzz.distance import Levenshtein

# --------- 基本設定 ---------
OLLAMA_URL_DEFAULT = "http://localhost:11434"
MODEL_DEFAULT = "qwen2.5vl:7b"

st.set_page_config(page_title="DocVQA Demo (Ollama + Qwen2.5VL)", layout="wide")

def call_ollama(images_b64: List[str], question: str, model: str, base_url: str) -> str:
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature":0},
        "messages": [
            {"role":"system","content":"You are a document QA assistant. Reply with the exact text span from the document only."},
            {"role":"user","content":"If answer not found, reply `unknown`.", "images": images_b64},
            {"role":"user","content": question}
        ]
    }
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()

def to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    # 保持原格式（png 較穩）
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def nls(a: str, b: str) -> float:
    a, b = a.strip(), b.strip()
    if not a and not b: return 1.0
    dist = Levenshtein.distance(a.lower(), b.lower())
    return 1.0 - dist / max(len(a), len(b) if len(b)>0 else 1)

def anls(pred: str, gold_list: List[str], tau: float=0.5) -> float:
    if not gold_list: return 0.0
    best = max(nls(pred, g) for g in gold_list)
    return best if best >= tau else 0.0

# --------- 側邊欄設定 ---------
with st.sidebar:
    st.header("設定")
    base_url = st.text_input("Ollama Base URL", value=OLLAMA_URL_DEFAULT)
    model = st.selectbox("模型", ["qwen2.5vl:3b","qwen2.5vl:7b"], index=1)
    st.caption("提示：4070/12GB 建議 7B；若顯存吃緊可改 3B。")
    st.divider()
    st.markdown("**服務檢查**")
    if st.button("Check /api/version"):
        try:
            vr = requests.get(f"{base_url}/api/version", timeout=10).json()
            st.success(vr)
        except Exception as e:
            st.error(f"無法連線：{e}")

st.title("📄 DocVQA Demo — Ollama + Qwen2.5VL")

tab1, tab2 = st.tabs(["🔍 單/多張互動", "📊 批量評測（ANLS）/ 產生 RRC 提交檔"])

# --------- Tab 1：單/多張互動 ---------
with tab1:
    st.subheader("上傳文件圖像並提問")
    imgs = st.file_uploader("上傳 1~N 張圖片（PNG/JPG）", type=["png","jpg","jpeg"], accept_multiple_files=True)
    q = st.text_input("問題（英文/中文皆可）", placeholder="What is the invoice number?")
    colA, colB = st.columns([1,1])
    with colA:
        run_btn = st.button("🚀 執行")
    with colB:
        clear_btn = st.button("🧹 清空輸出")

    if "results" not in st.session_state or clear_btn:
        st.session_state.results = []

    if run_btn and imgs and q.strip():
        images_b64 = []
        preview_cols = st.columns(min(4, len(imgs)))
        for i, up in enumerate(imgs):
            image = Image.open(up).convert("RGB")
            images_b64.append(to_b64(image))
            with preview_cols[i % len(preview_cols)]:
                st.image(image, caption=f"Image {i+1}", use_column_width=True)

        with st.spinner("模型推理中…"):
            try:
                ans = call_ollama(images_b64, q.strip(), model, base_url)
                st.success(ans)
                st.session_state.results.append({"question": q.strip(), "answer": ans})
            except Exception as e:
                st.error(f"推理失敗：{e}")

    if st.session_state.results:
        st.subheader("本次問答結果")
        st.table(st.session_state.results)
        # 下載 CSV/JSON
        import csv
        from io import StringIO
        csv_buf = StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=["question","answer"])
        writer.writeheader()
        writer.writerows(st.session_state.results)
        st.download_button("⬇️ 下載結果 (CSV)", csv_buf.getvalue().encode("utf-8"), "docvqa_results.csv", "text/csv")
        st.download_button("⬇️ 下載結果 (JSON)", json.dumps(st.session_state.results, ensure_ascii=False).encode("utf-8"),
                           "docvqa_results.json", "application/json")

# --------- Tab 2：批量評測（ANLS） ---------
with tab2:
    st.subheader("上傳驗證集 JSONL，批量推理並計算 ANLS")
    st.caption("預期欄位：questionId, image, question, answers（answers = 字串陣列）。image 建議使用本機路徑。")
    val_file = st.file_uploader("val.jsonl", type=["jsonl"], accept_multiple_files=False, key="valjsonl")
    tau = st.slider("ANLS 門檻 tau", 0.0, 1.0, 0.5, 0.05)
    go = st.button("📈 開始評測")

    if go and val_file is not None:
        lines = val_file.read().decode("utf-8").splitlines()
        data = [json.loads(x) for x in lines if x.strip()]
        prog = st.progress(0)
        scores, submit = [], []
        for i, ex in enumerate(data, start=1):
            # 讀圖：支援絕對/相對路徑
            img_path = ex["image"]
            if not os.path.isabs(img_path):
                # 以當前執行目錄為相對基準
                img_path = os.path.normpath(img_path)
            try:
                im = Image.open(img_path).convert("RGB")
            except Exception as e:
                st.error(f"[{ex.get('questionId')}] 圖片讀取失敗：{img_path} ({e})")
                pred = "unknown"
                scores.append(anls(pred, ex.get("answers", []), tau))
                submit.append({"questionId": ex["questionId"], "answer": pred})
                prog.progress(i/len(data))
                continue

            b64 = to_b64(im)
            try:
                pred = call_ollama([b64], ex["question"], model, base_url)
            except Exception as e:
                st.error(f"[{ex.get('questionId')}] 推理失敗：{e}")
                pred = "unknown"

            scores.append(anls(pred, ex.get("answers", []), tau))
            submit.append({"questionId": ex["questionId"], "answer": pred})
            prog.progress(i/len(data))

        mean_anls = round(statistics.mean(scores), 4) if scores else 0.0
        st.success(f"ANLS = {mean_anls}")

        # 下載 RRC 提交檔（通常是 list[ {questionId, answer} ] 的 JSON）
        st.download_button(
            "⬇️ 下載 RRC 提交檔 (JSON)",
            json.dumps(submit, ensure_ascii=False).encode("utf-8"),
            file_name="docvqa_submission.json",
            mime="application/json"
        )


# curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{ "model":"qwen2.5vl:7b", "messages":[{"role":"user","content":"hi"}], "stream":false }'
# curl -X POST http://localhost:11434/api/chat -H 'Content-Type: application/json' -d '{"model":"qwen2.5-vl","messages":[{"role":"user","content":"hi"}],"stream"}'
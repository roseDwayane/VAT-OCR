# -*- coding: utf-8 -*-
"""
Ollama 視覺分類：一次暖機，多次分類（重用 context / 減少 token 與延遲）

用法：
1) 先暖機（只需一次，之後可重用）：
   python ollama_fewshot_session_reuse.py --warmup

2) 分類單張影像：
   python ollama_fewshot_session_reuse.py ./invoice2.jpg

3) 批次分類資料夾內所有影像：
   python ollama_fewshot_session_reuse.py --dir ./inbox

說明：
- 暖機時送出系統規則 + few-shot 影像範例一次，取得並保存 model context（/tmp/ollama_ctx_qwen2p5vl.json）。
- 之後每次分類只送一張影像 + 簡短指令 + 上次回傳的 context，
  讓模型「記住」規則與範例，無需每次重發 few-shot，降低 token 與延遲。
- 若想清除並重建 context，加 --warmup 即可（會覆蓋原檔）。

備註：
- Ollama 的 chat 介面支援傳入/回傳 context；重用 context 可顯著降低提示長度與計算量。
- 若 Python 套件版本不接受 keep_alive/context 參數，可改用 requests 直接呼叫 /api/chat。
"""

from __future__ import annotations
import os
import sys
import json
import base64
from typing import List, Optional
try:
    import requests
except Exception as e:  # pragma: no cover
    raise RuntimeError("請先安裝 requests：pip install requests") from e

try:
    # 官方 ollama Python 客戶端（若版本不支援 context，將改走 REST）
    from ollama import chat as ollama_chat  # noqa: F401
except Exception:
    ollama_chat = None  # 允許缺省，走 REST


# === 可調參數 ===
MODEL = "qwen2.5vl:7b"     # 若顯存不足可改 "qwen2.5vl:3b"
CTX_PATH = "/tmp/ollama_ctx_qwen2p5vl.json"  # 保存 context 的本機檔案
# 依環境變數覆寫（與 ollama CLI 一致）
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
KEEP_ALIVE = "30m"          # 模型保留在記憶體時間
NUM_CTX = 8192               # 上下文長度（依機器與模型調整）


def img_to_b64(path: str) -> str:
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


# === 系統規則（可與 Modelfile 串接，見文末說明） ===
system_msg = (
    "You are a document understanding assistant. "
    "Classify the document into one of: "
    "['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',"
    "'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other']. "
    "Then extract fields into JSON with keys: doc_class, header, body, tail, rationale (optional). "
    "Amounts must be digits only (no commas). If unknown, use null or omit the property. "
    "Return JSON only, no extra text."
)

# === Few-shot：沿用你現有的 8 個影像範例與對應 JSON（保持與原邏輯一致） ===
#   提醒：例子中的 JSON 只是示意給模型參考，不會在本程式被解析。
#   若想最佳化效果，建議把例子修正成嚴格合法 JSON（例如補上漏掉的逗號或字串引號）。

# 你的 few-shot 樣本路徑（請確保存在）
ex_paths = [
    './few_shot_sample/image/1_business_invoice.jpg',
    './few_shot_sample/image/2_customs_tax_payment.jpg',
    './few_shot_sample/image/3_e_invoice.jpg',
    './few_shot_sample/image/4_plumb_payment_order.jpg',
    './few_shot_sample/image/5_tele_payment_order.jpg',
    './few_shot_sample/image/6_tradition_invoice.jpg',
    './few_shot_sample/image/7_triple_invoice.jpg',
    './few_shot_sample/image/8_triple_receipt.jpg',
]

# 你的 few-shot 回覆（為節省篇幅，示意以佔位文字；實作時請貼回你原始的 JSON 範例字串）
# 小技巧：若擔心上下文過長，可將 rationale 與長 Abstract 縮短，保留關鍵欄位即可。
example_answers = [
    """{\n  \"doc_class\": \"business_invoice\",\n  \"header\": {\"PrefixTwoLetters\": \"SX\"},\n  \"body\": {\"Abstract\": \"...\"},\n  \"tail\": {\"TotalAmount\": \"47390\"}\n}""",
    """{\n  \"doc_class\": \"customs_tax_payment\",\n  \"header\": {\"PrefixThreeLetters\": \"CXI\"},\n  \"body\": {\"Abstract\": \"海關進口\"},\n  \"tail\": {\"TotalAmount\": \"3536\"}\n}""",
    """{\n  \"doc_class\": \"e_invoice\",\n  \"header\": {\"PrefixTwoLetters\": \"RC\"},\n  \"body\": {\"InvoiceYear\": \"2021\"},\n  \"tail\": {\"TotalAmount\": \"80\"}\n}""",
    """{\n  \"doc_class\": \"plumb_payment_order\",\n  \"header\": {\"BuyerName\": \"彩琿實業有限公司\"},\n  \"tail\": {\"TotalAmount\": \"212\"}\n}""",
    """{\n  \"doc_class\": \"tele_payment_order\",\n  \"header\": {\"SerialNumber\": \"42518759\"},\n  \"tail\": {\"TotalAmount\": \"1229\"}\n}""",
    """{\n  \"doc_class\": \"tradition_invoice\",\n  \"header\": {\"InvoiceNumber\": \"03779651\"},\n  \"tail\": {\"TotalAmount\": \"195\"}\n}""",
    """{\n  \"doc_class\": \"triple_invoice\",\n  \"header\": {\"BuyerName\": \"建邦貿易有限公司\"},\n  \"tail\": {\"TotalAmount\": \"27069\"}\n}""",
    """{\n  \"doc_class\": \"triple_receipt\",\n  \"header\": {\"InvoiceNumber\": \"15255935\"},\n  \"tail\": {\"TotalAmount\": \"13201\"}\n}""",
]


def build_fewshot_messages() -> list:
    """建立一次性的 few-shot 對話訊息，用於暖機。"""
    messages = [{"role": "system", "content": system_msg}]
    for img_path, ans in zip(ex_paths, example_answers):
        if not os.path.exists(img_path):
            print(f"[警告] 找不到 few-shot 影像：{img_path}")
            b64 = None
        else:
            b64 = img_to_b64(img_path)
        messages.append({"role": "user", "content": "請分類這張文件", "images": [b64] if b64 else []})
        messages.append({"role": "assistant", "content": ans})
    # 清楚告知之後的互動規則，請模型只回覆 JSON。
    messages.append({
        "role": "user",
        "content": (
            "你已讀取 8 種範例。接下來我只會送一張影像，"
            "請直接輸出單一 JSON（不得有多餘文字）。若理解請回覆 READY。"
        ),
    })
    return messages


def chat_once(messages: list, fmt: Optional[str] = None, context: Optional[list] = None):
    """呼叫 Ollama /api/chat，支援 format/context/keep_alive/options。

    備註：部分 ollama Python 套件版本不接受 chat(context=...)，故統一改走 REST，
    以確保 context 能正確傳遞與回傳。
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "options": {"temperature": 0, "seed": 42, "num_ctx": NUM_CTX},
    }
    if fmt is not None:
        payload["format"] = fmt
    if context is not None:
        payload["context"] = context

    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    r = requests.post(url, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def save_context(ctx: list) -> None:
    os.makedirs(os.path.dirname(CTX_PATH), exist_ok=True)
    with open(CTX_PATH, "w", encoding="utf-8") as f:
        json.dump({"context": ctx}, f)


def load_context() -> Optional[list]:
    if not os.path.exists(CTX_PATH):
        return None
    try:
        with open(CTX_PATH, "r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj.get("context")
    except Exception:
        return None


def warmup() -> list:
    """送出系統規則 + few-shot 一次，並保存 context。"""
    messages = build_fewshot_messages()
    resp = chat_once(messages, fmt=None, context=None)
    # 取得 context 重用
    ctx = resp.get("context") or []
    save_context(ctx)
    print("[暖機完成] context 已保存。模型回覆：", resp.get("message", {}).get("content"))
    return ctx


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


def classify_image(img_path: str, ctx: Optional[list]) -> str:
    """使用既有 context 分類新影像，回傳 JSON 字串。"""
    if not os.path.exists(img_path):
        raise FileNotFoundError(img_path)

    b64 = img_to_b64(img_path)

    user_msg = (
        "請分析這張文件並輸出單一 JSON。"
        "1) 選擇 doc_class（上列九類其一）。"
        "2) 擷取 header/body/tail 相關欄位；不確定的設為 null 或省略。"
        "3) 僅輸出 JSON，不加解說。"
    )

    messages = [{"role": "user", "content": user_msg, "images": [b64]}]

    # 先嘗試 JSON 模式
    try:
        resp = chat_once(messages, fmt="json", context=ctx)
        content = resp.get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("空回覆")
        return content
    except Exception as e:
        # 退而求其次：非 JSON 格式，手動擷取第一段 JSON
        resp = chat_once(messages, fmt=None, context=ctx)
        raw = resp.get("message", {}).get("content", "")
        return _extract_first_json_block(raw)


def list_images_in_dir(d: str) -> List[str]:
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    files = []
    for name in os.listdir(d):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.path.splitext(name)[1].lower() in exts:
            files.append(p)
    return sorted(files)


if __name__ == "__main__":
    # 命令列介面
    if len(sys.argv) >= 2 and sys.argv[1] == "--warmup":
        warmup()
        sys.exit(0)

    # 載入或建立 context
    ctx = load_context()
    if ctx is None:
        print("[提示] 未找到既有 context，先進行一次暖機……")
        ctx = warmup()

    if len(sys.argv) >= 3 and sys.argv[1] == "--dir":
        # 批次分類
        directory = sys.argv[2]
        imgs = list_images_in_dir(directory)
        if not imgs:
            print(f"[訊息] {directory} 無影像檔")
            sys.exit(0)
        for p in imgs:
            out = classify_image(p, ctx)
            print("====", p)
            print(out)
            print()
    else:
        # 分類單檔（預設路徑可自行修改）
        img_path = sys.argv[1] if len(sys.argv) > 1 else "./invoice2.jpg"
        out = classify_image(img_path, ctx)
        print(out)


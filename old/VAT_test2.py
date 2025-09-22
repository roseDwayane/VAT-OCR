# VAT_OCR.py  —— 以 Unsloth FastVisionModel 進行推論，並保證輸出為可解析 JSON 字串
import re, json, ast
from typing import Tuple, Any, List, Optional
from PIL import Image

# ====== 1) 載入模型（僅載入一次）=========================================
from unsloth import FastVisionModel
_model = None
_tokenizer = None

def _load_model_once():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        # 這裡填你實際的模型路徑/名稱
        _model, _tokenizer = FastVisionModel.from_pretrained(
            model_name = "VAT_model",   # <- 你的 LoRA/合併後模型
            load_in_4bit = True,        # 需 bnb；若想 16-bit，改 False
        )
        FastVisionModel.for_inference(_model)  # Inference 模式
    return _model, _tokenizer

# ====== 2) 實用：擷取第一段 JSON 的幫手（和你原本名稱相容）==============
def _extract_first_json_block(text: str) -> str:
    """
    從文字中擷取第一個 {...} 或 [...] 的區塊；找不到就回原文。
    讓上層能在 LLM 有前後說明時仍抓到 JSON 主體。
    """
    t = text.strip()
    lb, rb = t.find("{"), t.rfind("}")
    if lb != -1 and rb != -1 and rb > lb:
        return t[lb:rb+1]
    lb, rb = t.find("["), t.rfind("]")
    if lb != -1 and rb != -1 and rb > lb:
        return t[lb:rb+1]
    return t

# ====== 3) JSON 修復器：把「幾乎 JSON」修成合法 JSON =====================
def _repair_json(s: str, schema: Optional[dict] = None) -> Tuple[str, Any, List[str]]:
    """
    將「幾乎 JSON」的字串修復成合法 JSON。
    回傳: (fixed_text, obj, logs)
      fixed_text: 修復後的 JSON 字串
      obj:        對應的 Python 物件 (dict/list)
      logs:       修復步驟紀錄
    """
    logs: List[str] = []
    text = s.strip()

    # 去掉 ```json ... ``` 殼
    if "```" in text:
        text = re.sub(r"```(?:json|JSON)?", "", text)
        text = text.replace("```", "").strip()
        logs.append("removed code fences")

    # 擷取外層 JSON 區塊
    text2 = _extract_first_json_block(text)
    if text2 != text:
        logs.append("extracted outer JSON-like region")
        text = text2

    # 先試標準 JSON
    try:
        obj = json.loads(text)
        logs.append("parsed by json")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"json.loads failed: {e}")

    # 再試 Python 字面量（單引號/尾逗號）
    try:
        obj = ast.literal_eval(text)
        logs.append("parsed by ast.literal_eval")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"ast.literal_eval failed: {e}")

    # 常見修補
    fixed = text.translate(str.maketrans({
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    }))
    if fixed != text:
        logs.append("normalized curly quotes")

    fixed2 = re.sub(r'(?<!")\bTrue\b(?!")', "true", fixed)
    fixed2 = re.sub(r'(?<!")\bFalse\b(?!")', "false", fixed2)
    fixed2 = re.sub(r'(?<!")\bNone\b(?!")', "null", fixed2)
    if fixed2 != fixed:
        logs.append("converted Python literals to JSON")
    fixed = fixed2

    fixed_no_trailing = re.sub(r",\s*([}\]])", r"\1", fixed)
    if fixed_no_trailing != fixed:
        logs.append("removed trailing commas")
    fixed = fixed_no_trailing

    dq = re.sub(r'(?<!\\)\'', '"', fixed)
    if dq != fixed:
        logs.append("replaced single quotes with double quotes")
    fixed = dq

    try:
        obj = json.loads(fixed)
        logs.append("fixed manually then parsed by json")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"final json.loads failed: {e}")
        fallback = {"raw": s}
        if schema:
            logs.append("returned raw because schema validation/parse failed")
        return json.dumps(fallback, ensure_ascii=False, indent=2), fallback, logs

# ====== 4) 正規化輸出鍵，保證有 header/body/tail 結構 ===================
def _normalize_llm_object(obj: Any) -> dict:
    """
    - 若是 { "gt_parse": {...} } 取內層
    - 接受 "Tail"/"tail" 大小寫
    - 僅保留 header/body/tail 三塊；不存在則補空物件
    """
    if not isinstance(obj, dict):
        return {"header": {}, "body": {}, "tail": {}}

    if "gt_parse" in obj and isinstance(obj["gt_parse"], dict):
        obj = obj["gt_parse"]

    header = obj.get("header", {}) or {}
    body   = obj.get("body",   {}) or {}
    tail   = obj.get("tail",   {}) or obj.get("Tail", {}) or {}

    # 可在這裡做金額/日期清洗（移除逗號、$）
    def _clean_num(v):
        if isinstance(v, str):
            v = v.replace(",", "").replace("，", "").replace("$", "").strip()
        return v

    if "SalesTax" in tail:         tail["SalesTax"] = _clean_num(tail["SalesTax"])
    if "TotalAmount" in tail:      tail["TotalAmount"] = _clean_num(tail["TotalAmount"])
    if "SalesTotalAmount" in tail: tail["SalesTotalAmount"] = _clean_num(tail["SalesTotalAmount"])

    return {
        "header": header,
        "body": body,
        "tail": tail,
    }

# ====== 5) 單張影像 → 讓模型說話 → 回傳「JSON 字串」 =====================
def infer_image_json(img_path: str) -> str:
    """
    讀入影像，呼叫 Unsloth 視覺模型，取得文字輸出，
    經修復/正規化後，**回傳 JSON 字串**（保持你原本測試碼的介面）。
    """
    model, tokenizer = _load_model_once()

    # 讀圖
    image = Image.open(img_path).convert("RGB")

    # 你的指令
    instruction = "你是發票/單據分類器與結構化抽取器，請辨識這張文件"

    # 構建聊天模板（<image> 由 apply_chat_template 插入）
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": instruction},
            ],
        }
    ]
    prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True)

    # 編碼（注意：無需手動把 <image> 放進 prompt；tokenizer 會處理）
    inputs = tokenizer(
        image,
        prompt,
        add_special_tokens=False,
        return_tensors="pt",
    ).to("cuda")

    # 產生（建議固定性：do_sample=False, temperature=0.0）
    gen_ids = model.generate(
        **inputs,
        max_new_tokens=512,
        use_cache=True,
        do_sample=False,
        temperature=0.0,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    # 只取新產生 tokens
    prompt_len = inputs["input_ids"].shape[1]
    new_token_ids = gen_ids[0, prompt_len:]
    raw_text = tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()

    # 先擷取 JSON 主體再嘗試解析/修復
    candidate = _extract_first_json_block(raw_text)

    try:
        obj = json.loads(candidate)
    except Exception:
        fixed_text, obj, _ = _repair_json(raw_text)
        candidate = fixed_text  # 回傳修復後的字串

    # 正規化成 header/body/tail 結構
    obj = _normalize_llm_object(obj)

    # 最終回傳「JSON 字串」，以符合你現有的 infer_and_flatten() 流程
    return json.dumps(obj, ensure_ascii=False)

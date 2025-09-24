if True:
    from unsloth import FastVisionModel
    model, tokenizer = FastVisionModel.from_pretrained(
        model_name = "VAT_model", # YOUR MODEL YOU USED FOR TRAINING
        load_in_4bit = True, # Set to False for 16bit LoRA
    )
    FastVisionModel.for_inference(model) # Enable for inference!

import re, json, ast
from typing import Tuple, Any, List, Optional

def repair_json(s: str, schema: Optional[dict] = None) -> Tuple[str, Any, List[str]]:
    """
    將「幾乎 JSON」的字串修復成合法 JSON。
    回傳: (fixed_text, obj, logs)
      fixed_text: 修復後的 JSON 字串
      obj:        對應的 Python 物件 (dict/list)
      logs:       修復步驟紀錄
    """
    logs: List[str] = []
    text = s.strip()

    # 0) 去掉 ```json ... ``` 或一般 ``` 區塊外殼
    if "```" in text:
        text = re.sub(r"```(?:json|JSON)?", "", text)
        text = text.replace("```", "")
        text = text.strip()
        logs.append("removed code fences")

    # 1) 只擷取最外層 {...} 或 [...]
    def _extract_json_region(t: str) -> str:
        lb, rb = t.find("{"), t.rfind("}")
        if lb != -1 and rb != -1 and rb > lb:
            return t[lb:rb+1]
        lb, rb = t.find("["), t.rfind("]")
        if lb != -1 and rb != -1 and rb > lb:
            return t[lb:rb+1]
        return t

    text2 = _extract_json_region(text)
    if text2 != text:
        logs.append("extracted outer JSON-like region")
        text = text2

    # 2) 嘗試標準 JSON
    try:
        obj = json.loads(text)
        logs.append("parsed by json")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"json.loads failed: {e}")

    # 3) 用 ast.literal_eval 吃單引號/尾逗號 等 Python 字面量
    try:
        obj = ast.literal_eval(text)
        logs.append("parsed by ast.literal_eval")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"ast.literal_eval failed: {e}")

    # 4) 常見修補：彎引號→直引號、True/False/None→JSON、刪尾逗號、單引號→雙引號
    fixed = text.translate(str.maketrans({
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    }))
    if fixed != text:
        logs.append("normalized curly quotes")

    # Python 常量 → JSON 常量
    fixed2 = re.sub(r'(?<!")\bTrue\b(?!")', "true", fixed)
    fixed2 = re.sub(r'(?<!")\bFalse\b(?!")', "false", fixed2)
    fixed2 = re.sub(r'(?<!")\bNone\b(?!")', "null", fixed2)
    if fixed2 != fixed:
        logs.append("converted Python literals to JSON")
    fixed = fixed2

    # 移除尾逗號
    no_trailing_commas = re.sub(r",\s*([}\]])", r"\1", fixed)
    if no_trailing_commas != fixed:
        logs.append("removed trailing commas")
    fixed = no_trailing_commas

    # 粗略：單引號 → 雙引號（在中文內容通常安全）
    dq = re.sub(r"(?<!\\)'", '"', fixed)
    if dq != fixed:
        logs.append("replaced single quotes with double quotes")
    fixed = dq

    # 5) 最終嘗試標準 JSON
    try:
        obj = json.loads(fixed)
        logs.append("fixed manually then parsed by json")
        if schema:
            from jsonschema import validate
            validate(obj, schema); logs.append("validated by jsonschema")
        return json.dumps(obj, ensure_ascii=False, indent=2), obj, logs
    except Exception as e:
        logs.append(f"final json.loads failed: {e}")
        # 兜底：包 raw
        fallback = {"raw": s}
        if schema:
            logs.append("returned raw because schema validation/parse failed")
        return json.dumps(fallback, ensure_ascii=False, indent=2), fallback, logs

import json, re
from typing import Any, Dict, Tuple, Mapping, Optional

def _extract_json(s: str) -> Dict[str, Any]:
    start = s.find("{"); end = s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("找不到可解析的 JSON 內容")
    return json.loads(s[start:end+1])

def _canonical_key_map(d: Dict[str, Any]) -> Dict[str, str]:
    # 建立不分大小寫的鍵名映射：lower(key) -> 原鍵名
    return {k.lower(): k for k in d.keys()}

def _get_ci(d: Dict[str, Any], key: str):
    # 不分大小寫取值；找不到返回 None
    if key in d: return d[key]
    lk = key.lower()
    for k in d.keys():
        if k.lower() == lk:
            return d[k]
    return None

def _is_none(x: Any) -> bool: return x is None
def _is_nonempty_str(x: Any) -> bool: return isinstance(x, str) and len(x.strip()) > 0
def _re_match(pattern: str, x: Any) -> bool:
    if x is None: return True          # 非必填且 None 視為 OK；是否必填由 required 控制
    if not isinstance(x, str): return False
    return re.fullmatch(pattern, x.strip()) is not None

def _amount_parse_and_normalize_int_str(x: Any) -> Optional[str]:
    """允許千分位與 .00；回傳正規化整數字串，否則 None。"""
    if not isinstance(x, str) or not x.strip():
        return None
    s = x.strip()
    # 允許 "123456", "1,234,567", "1,234,567.00"
    if re.fullmatch(r"\d{1,3}(,\d{3})*(?:\.00)?", s):
        s_no_comma = s.replace(",", "")
        if s_no_comma.endswith(".00"):
            s_no_comma = s_no_comma[:-3]
        try:
            return str(int(s_no_comma))
        except ValueError:
            return None
    # 允許無逗號但帶 .00
    if re.fullmatch(r"\d+(?:\.00)?", s):
        if s.endswith(".00"):
            s = s[:-3]
        try:
            return str(int(s))
        except ValueError:
            return None
    return None

def _normalize_year_to_gregorian(y: Any) -> Optional[str]:
    """2~3 碼視為民國年 +1911；4 碼視為西元年；其餘回 None。"""
    if not isinstance(y, str) or not y.strip() or not y.strip().isdigit():
        return None
    s = y.strip()
    if len(s) in (2, 3):  # 民國年
        return str(int(s) + 1911)
    if len(s) == 4:       # 西元年
        return s
    return None


def _strip_leading_zero_num_str(x: Any) -> Optional[str]:
    """將 '09' -> '9'；若非數字字串則回 None。"""
    if not isinstance(x, str) or not x.strip():
        return None
    s = x.strip()
    if not re.fullmatch(r"\d+", s):
        return None
    try:
        return str(int(s))
    except ValueError:
        return None

PAT_MM = r"(0?[1-9]|1[0-2])"
PAT_DD = r"(0?[1-9]|[12]\d|3[01])"

def check_compliance(
    data_or_str: Any,
    required_fields: Optional[Tuple[str, ...]] = None,
    required_fields_by_doc_class: Optional[Mapping[str, Tuple[str, ...]]] = None,
    only_required_and_rules: bool = True,
    emit_info: bool = True,  # 若要加上 @info，可設 True
    emit_normalized: bool = False,                  # ★ 會輸出 @normalized:*（三個金額欄位）
    return_normalized_object: bool = True,        # ★ 回傳 (結果, 正規化後物件)
) -> Dict[str, bool]:
    # 1) 解析
    if isinstance(data_or_str, str):
        obj = _extract_json(data_or_str)
    elif isinstance(data_or_str, dict):
        obj = data_or_str
    else:
        raise TypeError("只接受 dict 或 str (JSON)")

    # 2) 取出扁平的 gt_parse（若不在 gt_parse，則視為已是扁平）
    root = obj.get("gt_parse", obj)
    keymap = _canonical_key_map(root)
    # 支援 Doc_class / doc_class；Rationale / rationale
    doc_class_key = keymap.get("doc_class", "Doc_class" if "Doc_class" in root else "doc_class")
    rationale_key = keymap.get("rationale", "Rationale" if "Rationale" in root else "rationale")
    doc_class = _get_ci(root, doc_class_key)

    # 3) 欄位格式規則（扁平版）
    rules = {
        "PrefixTwoLetters":    lambda v: _re_match(r"[A-Z]{2}", v),
        "InvoiceNumber":       lambda v: _re_match(r"\d{8}", v),
        "InvoiceYear":         lambda v: _re_match(r"(\d{2,3}|\d{4})", v),
        "InvoiceMonth":        lambda v: _re_match(r"(0?[1-9]|1[0-2])", v),
        "InvoiceDay":          lambda v: _re_match(r"(0?[1-9]|[12]\d|3[01])", v),
        "BuyerName":           lambda v: True if v is None else _is_nonempty_str(v),
        "BuyerTaxIDNumber":    lambda v: True if v is None else _re_match(r"\d{8}", v),
        "CompanyName":         lambda v: True if v is None else _is_nonempty_str(v),
        "CompanyAddress":      lambda v: True if v is None else _is_nonempty_str(v),
        "CompanyTaxIDNumber":  lambda v: True if v is None else _re_match(r"\d{8}", v),
        "PhoneNumber":         lambda v: True if v is None else _re_match(r"[0-9()+\- ]{7,}", v),
        "Abstract":            lambda v: True if v is None else _is_nonempty_str(v),
        "SalesTotalAmount":    lambda v: (_amount_parse_and_normalize_int_str(v) is not None),
        "SalesTax":            lambda v: (_amount_parse_and_normalize_int_str(v) is not None),
        "TotalAmount":         lambda v: (_amount_parse_and_normalize_int_str(v) is not None),
        # meta
        doc_class_key:         lambda v: _is_nonempty_str(v) if v is not None else True,
        rationale_key:         lambda v: True if v is None else _is_nonempty_str(v),
    }

    # 4) 平面值（用輸入的實際鍵名；找不到就是 None）
    values = { k: root.get(k) for k in [
        "PrefixTwoLetters","InvoiceNumber","InvoiceYear","InvoiceMonth","InvoiceDay",
        "BuyerName","BuyerTaxIDNumber","CompanyName","CompanyAddress","CompanyTaxIDNumber",
        "PhoneNumber","Abstract","SalesTotalAmount","SalesTax","TotalAmount",
    ]}
    values[doc_class_key] = doc_class
    values[rationale_key] = _get_ci(root, rationale_key)

    # 5) 必填欄位（扁平版；可依需求調整）
    default_required = required_fields or (
        "PrefixTwoLetters","InvoiceNumber","SalesTotalAmount","SalesTax","TotalAmount",
    )
    per_class_required = required_fields_by_doc_class or {
        "triple_invoice": (
            "PrefixTwoLetters","InvoiceNumber", "BuyerTaxIDNumber",
            "InvoiceYear","InvoiceMonth","InvoiceDay", "Abstract",
            "SalesTotalAmount","SalesTax","TotalAmount", "CompanyTaxIDNumber",
        ),
        "triple_receipt": (
            "PrefixTwoLetters","InvoiceNumber", "CompanyTaxIDNumber",
            "InvoiceYear","InvoiceMonth","InvoiceDay", "BuyerTaxIDNumber",
            "Abstract",
            "SalesTotalAmount","SalesTax","TotalAmount",
        ),
    }
    active_required = per_class_required.get(str(doc_class), default_required)

    # 基本 + 必填
    full_result: Dict[str, bool] = {}
    for key, val in values.items():
        validator = rules.get(key, lambda v: True)
        ok = validator(val)
        if ok and key in active_required:
            ok = not _is_none(val) and (not isinstance(val, str) or len(val.strip()) > 0)
        full_result[key] = bool(ok)

    # 合計規則：以正規化後數值進行
    def _to_int_from_amount(x: Any) -> Optional[int]:
        norm = _amount_parse_and_normalize_int_str(x)
        if norm is not None:
            return int(norm)
        if isinstance(x, str) and re.fullmatch(r"\d+", x or ""):
            return int(x)
        return None

    st = _to_int_from_amount(values.get("SalesTotalAmount"))
    tax = _to_int_from_amount(values.get("SalesTax"))
    total = _to_int_from_amount(values.get("TotalAmount"))
    if None not in (st, tax, total):
        full_result["@rule:TotalAmount_equals_SalesTotal_plus_SalesTax"] = (st + tax == total)

    # 正規化輸出與物件（依 doc_class 組出「固定欄位 + 固定順序」）
    # 1) 先準備各欄位的正規化值
    st_norm = _amount_parse_and_normalize_int_str(values.get("SalesTotalAmount"))
    tax_norm = _amount_parse_and_normalize_int_str(values.get("SalesTax"))
    total_norm = _amount_parse_and_normalize_int_str(values.get("TotalAmount"))
    year_norm = _normalize_year_to_gregorian(values.get("InvoiceYear"))
    mm_norm = _strip_leading_zero_num_str(values.get("InvoiceMonth")) or values.get("InvoiceMonth")
    dd_norm = _strip_leading_zero_num_str(values.get("InvoiceDay")) or values.get("InvoiceDay")

    # 2) 建立以固定順序輸出的 gt_parse
    if str(doc_class) == "triple_receipt":
        normalized_gt_parse = {
            "Doc_class": "triple_receipt",
            "Rationale": _get_ci(root, "Rationale"),
            "PrefixTwoLetters": _get_ci(root, "PrefixTwoLetters"),
            "InvoiceNumber": _get_ci(root, "InvoiceNumber"),
            "CompanyName": _get_ci(root, "CompanyName"),
            "PhoneNumber": _get_ci(root, "PhoneNumber"),
            "CompanyTaxIDNumber": _get_ci(root, "CompanyTaxIDNumber"),
            "CompanyAddress": _get_ci(root, "CompanyAddress"),
            "InvoiceYear": _get_ci(root, "InvoiceYear"), # year_norm
            "InvoiceMonth": mm_norm,
            "InvoiceDay": dd_norm,
            "BuyerTaxIDNumber": _get_ci(root, "BuyerTaxIDNumber"),
            "BuyerName": _get_ci(root, "BuyerName"),
            "Abstract": _get_ci(root, "Abstract"),
            "SalesTotalAmount": st_norm if st_norm is not None else _get_ci(root, "SalesTotalAmount"),
            "SalesTax": tax_norm if tax_norm is not None else _get_ci(root, "SalesTax"),
            "TotalAmount": total_norm if total_norm is not None else _get_ci(root, "TotalAmount"),
        }
    else:  # 預設視為 triple_invoice（或其他類型也用這個順序以符合需求）
        normalized_gt_parse = {
            "Doc_class": "triple_invoice",
            "Rationale": _get_ci(root, "Rationale"),
            "PrefixTwoLetters": _get_ci(root, "PrefixTwoLetters"),
            "InvoiceNumber": _get_ci(root, "InvoiceNumber"),
            "BuyerName": _get_ci(root, "BuyerName"),
            "BuyerTaxIDNumber": _get_ci(root, "BuyerTaxIDNumber"),
            "InvoiceYear": _get_ci(root, "InvoiceYear"), # year_norm
            "InvoiceMonth": mm_norm,
            "InvoiceDay": dd_norm,
            "Abstract": _get_ci(root, "Abstract"),
            "SalesTotalAmount": st_norm if st_norm is not None else _get_ci(root, "SalesTotalAmount"),
            "SalesTax": tax_norm if tax_norm is not None else _get_ci(root, "SalesTax"),
            "TotalAmount": total_norm if total_norm is not None else _get_ci(root, "TotalAmount"),
            "CompanyName": _get_ci(root, "CompanyName"),
            "CompanyTaxIDNumber": _get_ci(root, "CompanyTaxIDNumber"),
            "PhoneNumber": _get_ci(root, "PhoneNumber"),
            "CompanyAddress": _get_ci(root, "CompanyAddress"),
        }

    normalized_obj = {"gt_parse": normalized_gt_parse}

    # 3) 在結果中標出三個金額欄位的正規化值（如有）
    if emit_normalized:
        if year_norm is not None:  full_result["@normalized:InvoiceYear"] = year_norm
        if mm_norm is not None: full_result["@normalized:InvoiceMonth"] = mm_norm
        if dd_norm is not None:   full_result["@normalized:InvoiceDay"] = dd_norm
        if st_norm is not None:    full_result["@normalized:SalesTotalAmount"] = st_norm
        if tax_norm is not None:   full_result["@normalized:SalesTax"] = tax_norm
        if total_norm is not None: full_result["@normalized:TotalAmount"] = total_norm

    # 只輸出必填 + 規則 + 正規化資訊
    if only_required_and_rules:
        filtered = {k: v for k, v in full_result.items()
                    if k in active_required or k.startswith("@rule:") or k.startswith("@normalized:") or (emit_info and k.startswith("@info:"))}
    else:
        filtered = full_result

    return (filtered, normalized_obj) if return_normalized_object else filtered


from pathlib import Path
from PIL import Image

FastVisionModel.for_inference(model)  # inference 模式


def chat_once(image_path):
    image = Image.open(image_path).convert("RGB")
    instruction = "你是發票/單據分類器與結構化抽取器，請辨識這張文件"

    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": instruction}
        ]}
    ]

    # 準備輸入
    input_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    inputs = tokenizer(
        image,
        input_text,
        add_special_tokens=False,
        return_tensors="pt",
    ).to("cuda")

    # 產生（不使用 streamer，改成一次取回）
    gen_ids = model.generate(
        **inputs,
        max_new_tokens=512,
        use_cache=True,
        temperature=0.1,
        min_p=0.1,
        do_sample=True,              # 若你想要可重現，可改成 False
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    # 只取「模型新產生」的 token，排除提示部分
    prompt_len = inputs["input_ids"].shape[1]
    new_token_ids = gen_ids[0, prompt_len:]

    output_text = tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()

    try:
        result = json.loads(output_text)
    except Exception:
        result, obj, logs = repair_json(output_text)

    return result


input_string = json.loads(chat_once("./invoice2.jpg"))
compliance, edit_string = check_compliance(input_string)
print(type(compliance))
print(json.dumps(compliance, ensure_ascii=False, indent=2))
print(json.dumps(edit_string, ensure_ascii=False, indent=2))

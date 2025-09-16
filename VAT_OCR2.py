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
    

from pathlib import Path
import json
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

print(chat_once("./invoice2.jpg"))

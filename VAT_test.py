import os
import json
from tqdm import tqdm
from PIL import Image
from collections import OrderedDict

# Import inference helpers from docvqa_final2
from docvqa_final2 import infer_image_json, _extract_first_json_block, chat_once, build_messages_for_image, img_to_b64  # noqa: F401


def extract_ground_truth(d: dict) -> dict:
    # 依指定順序輸出 9 個欄位；缺值給空字串
    out = OrderedDict()
    tail = d.get("Tail", {}) or d.get("tail", {})
    out["PrefixTwoLetters"]   = d.get("header", {}).get("PrefixTwoLetters", "")
    out["InvoiceNumber"]      = d.get("header", {}).get("InvoiceNumber", "")
    out["CompanyTaxIDNumber"] = d.get("body", {}).get("CompanyTaxIDNumber", "")
    out["BuyerTaxIDNumber"]   = d.get("body", {}).get("BuyerTaxIDNumber", "")
    out["InvoiceYear"]        = d.get("body", {}).get("InvoiceYear", "")
    out["InvoiceMonth"]       = d.get("body", {}).get("InvoiceMonth", "")
    out["InvoiceDay"]         = d.get("body", {}).get("InvoiceDay", "")
    out["SalesTax"]           = tail.get("SalesTax", "")
    out["TotalAmount"]        = tail.get("TotalAmount", "")
    return out


def infer_and_flatten(img_path: str) -> dict:
    """Call docvqa model once and return 9-field flat dict."""
    content = infer_image_json(img_path)
    try:
        data = json.loads(content)
    except Exception:
        # 容錯：擷取第一段 JSON 再 parse
        data = json.loads(_extract_first_json_block(content))
    return extract_ground_truth(data)

def diff_flat(a: dict, b: dict):
    diffs = []
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            diffs.append((k, a.get(k), b.get(k)))
    return diffs

# Initialize paths and counters
root_dir = '../AllDataset/VAT-OCR/triple_receipt/' #triple_invoice_dataset, triple_receipt
mode = 'test'
entries = os.listdir(os.path.join(root_dir, 'label', mode))

fail_count = 0
five_count = 0
six_count = 0
seven_count = 0
alright_count = 0
error_dict = {
    'PrefixTwoLetters': 0,
    'InvoiceNumber': 0,
    'InvoiceYear': 0,
    'InvoiceMonth': 0,
    'InvoiceDay': 0,
    'SalesTotalAmount': 0,
    'SalesTax': 0,
    'CompanyTaxIDNumber': 0
}

error = 0
# Process each entry
for entry in tqdm(entries, desc="Processing entries"):
    json_path = os.path.join(root_dir, 'label', mode, entry)
    img_name = os.path.splitext(entry)[0]
    img_path = os.path.join(root_dir, 'image', img_name + '.jpg')
        
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            ground_truth_data = json.load(file)
            #print("[debug] original: ", ground_truth_data)
        
        gtd = extract_ground_truth(ground_truth_data)
        #print("[debug] after process: ", json.dumps(gtd, ensure_ascii=False, indent=2))

        # Load image to get dimensions
        image = Image.open(img_path)
        # 進行一次推論，並取出 9 欄位
        pred9 = infer_and_flatten(img_path)
        #print(json.dumps(pred9, ensure_ascii=False, indent=2))

        if gtd != pred9:
            for k, va, vb in diff_flat(gtd, pred9):
                print(f"{k}: {va} != {vb}")
                error_dict[k] = error_dict[k] +1
        #ground_truth_data = extract_ground_truth(ground_truth_data)

        # Calculate accuracy
        #val_acc = calculate_accuracy(output, ground_truth_data)

    except:
        error = error +1
        continue
    
print(error)
"""
    # Update counters based on accuracy
    if val_acc < 60:
        fail_count += 1
        print(f"Fail: {img_path}")
    if val_acc >= 60:
        five_count += 1
    if val_acc >= 75:
        six_count += 1
    if val_acc >= 80:
        seven_count += 1
    if val_acc == 100:
        alright_count += 1

# Calculate total accuracy percentages
total_entries = len(entries)
print(f"Fail: {fail_count / total_entries * 100:.2f}%")
print(f"Five (>=60): {five_count / total_entries * 100:.2f}%")
print(f"Six (>=75): {six_count / total_entries * 100:.2f}%")
print(f"Seven (>=80): {seven_count / total_entries * 100:.2f}%")
print(f"Alright (100): {alright_count / total_entries * 100:.2f}%")
print("Error Dict:", error_dict)
"""
# 1. 抽取 ground truth
# 1. PrefixTwoLetters
# 2. InvoiceNumber
# 3. CompanyTaxIDNumber
# 4. BuyerTaxIDNumber
# 5. InvoiceYear
# 6. InvoiceMonth
# 7. InvoiceDay
# 8. SalesTax
# 9. TotalAmount
# 2. 解析 predict
# 3. 對比 答案
# 4. 紀錄錯幾格 與 哪幾格

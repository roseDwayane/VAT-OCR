# 文件定義

- 發票種類定義如下：
```
doc_class ∈ 
    ['triple_invoice', # 三聯式
    'triple_receipt', # 三收銀
    'business_invoice', # 證明聯
    'tradition_invoice', # 傳統發票
    'e_invoice', # 電子發票
    'plumb_payment_order', # 水電帳單
    'tele_payment_order', # 電信帳單
    'customs_tax_payment', # 海關進口
    'other']
```
> 目前 穩定支援 `triple_invoice, triple_receipt, business_invoice, tradition_invoice, e_invoice`

* 穩定支援欄位如下：
```
{
*   "Doc_class": "triple_invoice",
    "Rationale": "統一發票(三聯式)",
*   "PrefixTwoLetters": "KY",
*   "InvoiceNumber": "51981199",
    "BuyerName": "建邦貿易有限公司",
*   "BuyerTaxIDNumber": "12361788",
*   "InvoiceYear": "112",
*   "InvoiceMonth": "4",
*   "InvoiceDay": "30",
*   "Abstract": "皮帶 5 230 1150 皮帶 3 135 405 皮帶 1 105 105",
*   "SalesTotalAmount": "1660",
*   "SalesTax": "83",
*   "TotalAmount": "1743",
    "CompanyName": "合飛企業有限公司",
*    "CompanyTaxIDNumber": "12528062",
    "PhoneNumber": "02-25012804",
    "CompanyAddress": "台北市建國北路三段113巷7弄13號"
}

```
> 星號為必填欄位

# 核心技術
- 主要採用 [Qwen2.5-VL 7B](https://arxiv.org/pdf/2502.13923) 視覺語言模型，搭配 Ollama 伺服流程與 [Unsloth FastVisionModel](https://github.com/unslothai/unsloth) 進行 [LoRA fine-tune](https://arxiv.org/pdf/2106.09685)。
- 訓練加速：`unsloth` + PyTorch 2.8 (CUDA 12.6)，支援 4-bit/16-bit 載入、LoRA rank 調整與 gradient checkpointing。
- 結構化輸出：借助 `pydantic` schema、`jsonschema` 驗證與 `repair_json` 後處理，確保回傳合法 JSON 並保留修復日誌。
- 推論部署：
	- `ollama_fewshot_session_reuse.py` 透過 REST API 重用 context，降低每次請求的 prompt token 數。
	- `VAT_OCR2.py` 直接載入 `VAT_model` Adapter 於本地 GPU 推論。
	- `docvqa/` 內附 CLI (`docvqa_basic.py`) 與 `streamlit_app.py` GUI，方便互動測試。

# 製作資料集
- 以 `few_shot_sample/` 內的 8 類票據為 prompt 範本，資料夾架構如下：
  ```
  few_shot_sample/
    image/  # 提供八張示例影像 (1~8 對應各票據類型)
    label/  # 預留同名 JSON，實際標註與訓練採用 ../AllDataset/VAT-OCR 下資料
  ```
- 資料結構依票據種類分層存放，例如 `triple_receipt`：
  ```
  ../AllDataset/VAT-OCR/
    ├─triple_receipt/
    │   ├─image/                # 原始影像
    │   └─label/
    │       ├─train/            # 標註 JSON
    │       ├─test/
    │       ├─train_new/        # 不同版本標註，供實驗切換
    │       └─train_fail/...    # 問題樣本或調整紀錄
    ├─triple_invoice/
    └─...
  ```
- `../AllDataset/VAT-OCR/data_json.ipynb` 將標註轉換為 Donut 相容格式，輸出 `train_donut_dataset.json`, `train_new_donut_dataset.json`, `val_donut_dataset.json` 供 Hugging Face / Unsloth 讀取。
- `dataset_browser.py` (與 `dataset_browser_old.py`) 提供影像 + JSON 對照檢視工具，協助檢查標註欄位與字串格式。
- few-shot 樣本維持與主資料集一致的命名規則，方便在 prompt、warmup context 或測試腳本之間共用。

# LoRA fine-tune
- `VAT_Qwen2_5vl7B_lora_finetune.ipynb` 流程：
  1. 建立環境：載入 `FastVisionModel.from_pretrained("VAT_model" 或原始 Qwen2.5VL)`，設定 4-bit/16-bit、LoRA rank、learning rate 等超參。
  2. 載入 `train_new_donut_dataset.json` 等資料集，套用影像前處理與 chat template，建立 vision-language dataloader。
  3. 以 Unsloth Trainer 執行訓練與評估，並透過梯度檢查點、混合精度等選項最佳化 GPU 使用。
  4. 訓練完成後匯出 Adapter 至 `VAT_model/`（`adapter_model.safetensors`, `tokenizer.json`...），供推論與 Ollama 整合。

# Inference
- `VAT_finetune_inference.ipynb`：
	- 載入 `VAT_model` Adapter，提供單張或批次推論、`repair_json` 修復、欄位對齊 (`OrderedDict`) 以及錯誤統計。
	- 可直接連結資料集影像與標註，快速檢視模型輸出差異。
- 最終對接文件`VAT_OCR.py`：
	- 腳本開頭同樣透過 `Unsloth FastVisionModel.from_pretrained("VAT_model", load_in_4bit=True)` 載入 LoRA Adapter，並以 `FastVisionModel.for_inference` 讓模型進入推論設定（VAT_OCR.py:1）。
	- `repair_json` 與 notebook 版本一致：先移除區塊、擷取 JSON 區段，再依序嘗試 `json.loads／ast.literal_eval`，失敗時進行常見符號修補並保留操作紀錄，最終保證回傳可解析結果或原始字串（VAT_OCR.py:12）。
	- `chat_once` 接受圖片路徑後開啟影像、組合「你是發票欄位抽取器」的 user prompt，使用 tokenizer 建立 chat template，送入 GPU 生成 512 個 token 上限的回覆並解碼（VAT_OCR.py:118）。
	- 生成文本先嘗試 `json.loads`，若報錯則呼叫 `repair_json`，因此輸出永遠是 JSON 字串（同時附帶修復 log 供除錯）（VAT_OCR.py:154）。
	- 檔尾用 `print(chat_once("./invoice2.jpg"))` 做為 CLI 示範，方便快速確認模型是否正常回傳結構化結果（VAT_OCR.py:163）。


# 合規檢查
- `VAT_finetune_inference.ipynb` 內建欄位驗證流程：
	- `repair_json` 逐步記錄修復動作，確保鍵名、資料型別、數值格式符合 schema。
	- `check_compliance` 進行合法性檢查：先統一鍵名大小寫，再用 regex 驗證 9 個核心欄位、補缺欄位、統一 doc_class，同時支援 @info、@normalized 標記方便審計
```
{
  "PrefixTwoLetters": true,
  "InvoiceNumber": true,
  "InvoiceYear": true,
  "InvoiceMonth": true,
  "InvoiceDay": true,
  "BuyerTaxIDNumber": true,
  "CompanyTaxIDNumber": true,
  "Abstract": true,
  "SalesTotalAmount": true,
  "SalesTax": true,
  "TotalAmount": true,
  "@rule:TotalAmount_equals_SalesTotal_plus_SalesTax": true
}
```
- `VAT_test.py` 提供 ground truth 對照、逐欄列印差異與錯誤統計，支援內部稽核與回歸測試。

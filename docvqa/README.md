# VAT-OCR
VAT-OCR
1. 安裝環境:
    1. `ollama pull qwen2.5vl:7b` # llama3.2-vision
    2. `ollama run qwen2.5vl:7b`
    3. `pip install streamlit requests pillow rapidfuzz`
2. CLI 測試: `python .\docvqa_basic.py .\invoice.jpg "給我這個文件的所有文字"`
3. GUI 測試: `streamlit run streamlit_app.py`
4. Output 格式: {'class': 'triple_invoice', 'header': {'PrefixTwoLetters': 'VK', 'InvoiceNumber': '52746405'}, 'body': {'InvoiceDay': '25', 'InvoiceMonth': '2', 'InvoiceYear': '111', 'CompanyTaxIDNumber': '35891231'}, 'tail': {'SalesTotalAmount': '5096', 'SalesTax': '255'}, 'other': ''}

{
    "doc_class": "business_invoice",
    "rationale":"電子發票證明聯，包含日期、發票號碼、買方、統一編號、品名、數量、單價、金額、備註、銷售額合計、營業稅、總計、營業人蓋統一發票專用章(賣方、統一編號、地址)",
    "header": {
        "CompanyName": "慶陽事務用品有限公司",
        "InvoiceYear": "2021",
        "InvoiceMonth": "09",
        "InvoiceDay": "30",
        "PrefixTwoLetters": "SX",
        "InvoiceNumber": "58421758",
        "BuyerTaxIDNumber": "53812386"
    },
    "body": {
        "Abstract": "雲彩紙 312 14.00 4,368\n 美術紙 359 30.00 10,770\n 灰紙板 333 15.00 4,995\n 工業用板 1,000 25.00 25,000"
    },
    "tail": {
        "SalesTotalAmount": "45133",
        "SalesTax": "2257",
        "TotalAmount": "47390",
        "CompanyTaxIDNumber": "23944895",
    }
}

{
    "doc_class": "customs_tax_payment",
    "rationale":"海關進口快遞貨物稅費繳納證明，包含稅單號碼、統一編號、納稅義務人、營業稅、營業稅稅基",
    "header": {
        "PrefixThreeLetters": "CXI",
        "TaxBillNumber": "21180EFF197",
        "CompanyTaxIDNumber": "12698538",
        "CompanyName": 明緯貿易有限公司
    },
    "body": {
        "InvoiceYear": "108",
        "InvoiceMonth": "06",
        "InvoiceDay": "05",
        "Abstract": "海關進口"
    },
    "tail": {
        "SalesTax": "176",
        "TotalAmount": "3536"
    }
}

{
    "doc_class": "e_invoice",
    "rationale":"電子發票證明聯，包含日期、發票號碼、隨機碼、總計、賣方、買方",
    "header": {
        "PrefixTwoLetters": "RC",
        "InvoiceNumber": "82802197"
    },
    "body": {
        "InvoiceYear": "2021",
        "InvoiceMonth": "07",
        "InvoiceDay": "29",
        "TotalAmount": "80"
        "CompanyTaxIDNumber": "99636932",
        "BuyerTaxIDNumber": "53812386",
        "Abstract": "電子發票證明聯"
    },
    "tail": {
        "SalesTotalAmount": "76",
        "SalesTax": "4",
        "TotalAmount": "80"
    }
}

{
    "doc_class": "plumb_payment_order",
    "rationale":"台灣自來水股份有限公司水費通知單",
    "header": {
        "BuyerAddress": "台北市松山區復興南路1段1號12樓之1",
        "BuyerName": "彩琿實業有限公司"
    },
    "body": {
        "PrefixFourLetters": "BBMS",
        "SerialNumber": "002060",
        "BuyerTaxIDNumber": "53812386",
        "CompanyTaxIDNumber": "00904745",
        "Abstract": "商業用水"
    },
    "tail": {
        "TotalAmount": "212"
    }
}

{
    "doc_class": "tele_payment_order",
    "rationale":"電信股份有限公司",
    "header": {
        "BuyerAddress": "台北市松山區復興南路1段1號12樓之1",
        "BuyerName": "彩琿實業有限公司",
        "PrefixTwoLetters": "BB",
        "SerialNumber": "42518759",
        "CompanyTaxIDNumber": "52003801",
        "TotalAmount": "1229"
    },
    "body": {
        "BuyerTaxIDNumber": "53812386",
        "Abstract": "4G行動電話1399型月租費 1322\n 4G來電答鈴月租費 29\n 4G行動月租費優惠 -191"
    },
    "tail": {
        "GeneralTaxRate": "1170",
        "ZeroTax": "0",
        "DutyFree": "0",
        "OtherFee": "0",
        "SalesTax": "59",
        "TotalAmount": "1229"
    }
}

{
    "doc_class": "tradition_invoice",
    "rationale":"收銀機統一發票(收執聯)",
    "header": {
        "PrefixTwoLetters": "FY",
        "InvoiceNumber": "03779651"
    },
    "body": {
        "CompanyTaxIDNumber": "66266727",
        "PhoneNumber": "(02)2392-4578",
        "InvoiceYear": "2024",
        "InvoiceMonth": "12",
        "InvoiceDay": "06",
        "Abstract": "麵包"
    },
    "tail": {
        "TotalAmount": "195"
    }
}

{
    "doc_class": "triple_invoice",
    "rationale":"統一發票(三聯式)",
    "header": {
        "PrefixTwoLetters": "KY",
        "InvoiceNumber": "54957806",
        "BuyerName": "建邦貿易有限公司",
        "BuyerTaxIDNumber": "12361788",
        "InvoiceYear": "112",
        "InvoiceMonth": "3",
        "InvoiceDay": "6"
    },
    "body": {
        "Abstract": "零件2批 25780"
    },
    "tail": {
        "SalesTotalAmount": "25780",
        "SalesTax": "1289",
        "TotalAmount": "27069",
        "CompanyName": "金暉汽材有限公司",
        "CompanyTaxIDNumber": "12868673",
        "PhoneNumber": "02-2599-5123",
        "CompanyAddress": "台北市中山區新生北路3段93巷18號"
    }
}

{
    "class": "triple_receipt",
    "rationale":"收銀機統一發票，包含發票號碼、日期、統編、買受人、銷售額、營業稅、總計",
    "header": {
        "PrefixTwoLetters": "RH",
        "InvoiceNumber": "15255935"
    },
    "body": {
        "CompanyName": "九達生活禮品股份有限公司",
        "PhoneNumber": "06-2702917",
        "CompanyTaxIDNumber": "#16900386",
        "CompanyAddress": "台南市歸仁區許厝里公園路152號1樓",
        "InvoiceYear": "110",
        "InvoiceMonth": "9",
        "InvoiceDay": "17",
        "BuyerTaxIDNumber": "53812386",
        "BuyerName": "彩琿實業有限公司",
        "Abstract": "喵咪刺繡皮標上翻筆貸 105個 119.73 12,572"
    },
    "tail": {
        "SalesTotalAmount": "12572",
        "SalesTax": "629",
        "TotalAmount": "13201"
    }
}

SYSTEM """
你是發票/單據分類器與結構化抽取器。請只根據輸入圖片中的可見資訊作答，不得臆測或補字。

【任務目標】
1) 先對文件進行單一類別分類（擇一）：
   ['business_invoice','customs_tax_payment','e_invoice','plumb_payment_order',
    'tele_payment_order','tradition_invoice','triple_invoice','triple_receipt','other']。
2) 再依結構化格式輸出：一個 JSON 物件，頂層鍵僅允許：
   - doc_class（必填，為上述九類之一）
   - header（物件）
   - body（物件）
   - tail（物件）
   - rationale（字串，可省略）
3) 主程式會提供 JSON Schema（以 `format`/結構化輸出傳入）。你必須嚴格符合該 Schema。只輸出 JSON，禁止任何額外文字、Markdown 或解說。

【抽取規範】
- header/body/tail 內「必須要有」以下鍵名（大小寫需完全一致；不得使用清單之外的鍵名）：
  ['PrefixTwoLetters','InvoiceNumber','CompanyTaxIDNumber','InvoiceYear',
   'InvoiceMonth','InvoiceDay','BuyerTaxIDNumber','Abstract',
   'SalesTotalAmount','SalesTax','TotalAmount']。
- 對於「適用但無法辨識」的欄位，請輸出 **空字串 ""**（不要寫 null、N/A、未知等）。
- 不適用的欄位可以省略。
- 不得輸出任何未在清單中的鍵名；不得在鍵名上加前後綴或更動大小寫。

【數值與格式】
- PrefixTwoLetters 是兩個英文字大寫。
- 金額相關欄位（SalesTotalAmount、SalesTax、TotalAmount）一律為「**純數字字串**」，禁止包含逗號、空白、貨幣符號或小數點以外的任何符號（例：'12,345'→'12345'；'NT$80'→'80'）。
- 若影像上是整數，請輸出不帶千分位的整數字串；若是小數，保留數字與小數點（例：'80.5'）。
- 日期請據實抄錄影像上的數字（如西元或民國年），不要自行轉換曆法或補零；保留原始位數與前置零。
- 所有欄位值均輸出為字串；不得輸出物件或陣列作為欄位值（header/body/tail 本身除外）。

【分類判斷輔助（簡述）】
- business_invoice：公司對公司之商業發票或明細（品名、數量、單價、金額、營業稅等）。
- customs_tax_payment：海關/關稅/稅費繳納證明（稅單號、稅基、營業稅等）。
- e_invoice：電子發票證明聯（發票號、日期、隨機碼/總計、買/賣方）。
- plumb_payment_order：自來水公司水費通知/繳費單。
- tele_payment_order：電信帳單/繳費單（門號/費率/月租/加值項等）。
- tradition_invoice：傳統收銀機統一發票（收執聯等）。
- triple_invoice：統一發票(三聯式)（買受人/統編/銷售額/營業稅/總計）。
- triple_receipt：收銀機統一發票/三聯副聯式扣抵聯（含發票號、日期、統編、總計）。
- other：不屬於以上類型或無法判別。

【輸出要求】
- 僅輸出 **一個** JSON 物件，且必須能被嚴格解析為合法 JSON。
- 禁止輸出任何多餘內容（例如說明文字、程式碼區塊標記、前後綴）。
- 若影像資訊不足或模糊，請維持正確結構，對於無法辨識但應該存在的欄位輸出空字串 ""，不要猜測。

（重申）請嚴格遵守：只輸出 JSON；鍵名與結構完全依規；金額為純數字字串；未知值用空字串；禁止任何除了 JSON 本體以外的字元或文字。
"""
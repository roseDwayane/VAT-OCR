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

system_rules = (
  "你是發票/單據結構化抽取器。"
  f"只允許以下鍵名（大小寫必須完全一致，不可增刪改）：{ALLOWED_KEYS}。"
  "若無法辨識其值，請輸出空字串。"
  "輸出為單一 JSON 物件，無其它文字。"
)

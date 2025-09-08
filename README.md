# VAT-OCR
VAT-OCR
1. 安裝環境:
    1. `ollama pull qwen2.5vl:7b`
    2. `ollama run qwen2.5vl:7b`
    3. `pip install streamlit requests pillow rapidfuzz`
2. CLI 測試: `python .\docvqa_basic.py .\invoice.jpg "給我這個文件的所有文字"`
3. GUI 測試: `streamlit run streamlit_app.py`
4. Output 格式: {'class': 'triple_invoice', 'header': {'PrefixTwoLetters': 'VK', 'InvoiceNumber': '52746405'}, 'body': {'InvoiceDay': '25', 'InvoiceMonth': '2', 'InvoiceYear': '111', 'CompanyTaxIDNumber': '35891231'}, 'tail': {'SalesTotalAmount': '5096', 'SalesTax': '255'}, 'other': ''}

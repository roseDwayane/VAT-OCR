# VAT-OCR
VAT-OCR
1. 安裝環境:
    1. `ollama pull qwen2.5vl:7b`
    2. `ollama run qwen2.5vl:7b`
    3. `pip install streamlit requests pillow rapidfuzz`
2. CLI 測試: `python .\qwen_test.py .\invoice.jpg "請問這張圖片中的 1. 發票字軌(兩個英文字母) 2. 發票號碼 3. 統編 4. 日期 5. 買受人 6. 銷售額 7. 營業稅 8. 總計"`
3. GUI 測試: `streamlit run app_streamlit_docvqa.py`
4. Output 格式: {'class': 'triple_invoice', 'header': {'PrefixTwoLetters': 'VK', 'InvoiceNumber': '52746405'}, 'body': {'InvoiceDay': '25', 'InvoiceMonth': '2', 'InvoiceYear': '111', 'CompanyTaxIDNumber': '35891231'}, 'tail': {'SalesTotalAmount': '5096', 'SalesTax': '255'}, 'other': ''}

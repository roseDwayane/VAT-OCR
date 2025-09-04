# VAT-OCR
VAT-OCR
1. 安裝環境:
    1. `ollama pull qwen2.5vl:7b`
    2. `ollama run qwen2.5vl:7b`
    3. `pip install streamlit requests pillow rapidfuzz`
2. CLI 測試: `python .\qwen_test.py .\invoice.jpg "請給我整張圖片完整的資訊"`
3. GUI 測試: `streamlit run app_streamlit_docvqa.py`
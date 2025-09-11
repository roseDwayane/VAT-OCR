import json

j1 = """
{
  "PrefixTwoLetters": "GE",
  "InvoiceNumber": "24037960",
  "CompanyTaxIDNumber": "24231255",
  "BuyerTaxIDNumber": "53812386",
  "InvoiceYear": "109",
  "InvoiceMonth": "11",
  "InvoiceDay": "01",
  "SalesTax": "37",
  "TotalAmount": "777"
}
"""

j2 = """
{
  "PrefixTwoLetters": "GE",
  "InvoiceNumber": "24037960",
  "CompanyTaxIDNumber": "24231255",
  "BuyerTaxIDNumber": "53812386",
  "InvoiceYear": "109",
  "InvoiceMonth": "11",
  "InvoiceDay": "01",
  "SalesTax": "33",
  "TotalAmount": "777",
  "test2": "777"
}
"""

def diff_flat(a: dict, b: dict):
    diffs = []
    for k in set(a) | set(b):
        print(k)
        if a.get(k) != b.get(k):
            diffs.append((k, a.get(k), b.get(k)))
    return diffs




a = json.loads(j1)
b = json.loads(j2)
print(a == b)  # True（你的兩段內容相同）

if a != b:
    for k, va, vb in diff_flat(a, b):
        print(f"{k}: {va} != {vb}")

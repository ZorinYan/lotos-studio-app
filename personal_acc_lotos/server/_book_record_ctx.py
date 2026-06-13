import re
import requests

text = requests.get("https://n1996926.yclients.com/main-TSJIUNFL.js", timeout=60).text
idx = 0
while True:
    idx = text.find("book_record", idx)
    if idx < 0:
        break
    print("---", idx)
    print(repr(text[max(0, idx - 200) : idx + 400]))
    idx += 1

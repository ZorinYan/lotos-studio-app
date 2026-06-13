import re
import requests

text = requests.get("https://n1996926.yclients.com/main-TSJIUNFL.js", timeout=60).text
paths = sorted(set(re.findall(r'[`"\'][/][a-zA-Z0-9_/${}.?=&:-]+[`"\']', text)))
for p in paths:
    s = p.strip("`\"'")
    if "book" in s.lower() or "trial" in s.lower() or "activity" in s.lower():
        print(s)

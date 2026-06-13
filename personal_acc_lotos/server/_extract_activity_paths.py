import re
import requests

url = "https://n1996926.yclients.com/main-TSJIUNFL.js"
text = requests.get(url, timeout=60).text

for match in re.finditer(r"/activity/[^\"']{0,120}", text):
    print(match.group())

print("--- book snippets ---")
for match in re.finditer(r".{0,40}/book.{0,80}", text):
    snippet = match.group()
    if "activity" in snippet.lower() or "trial" in snippet.lower():
        print(snippet)

import re
import requests

text = requests.get(
    "https://n1996926.yclients.com/activity-flow-HJGZAQ2Q.js", timeout=60
).text

for needle in ["isTrial", "isTrialVisit", "VisitType.Trial", "book_record", "attendances"]:
    print(f"\n### {needle}")
    idx = 0
    n = 0
    while n < 8:
        idx = text.find(needle, idx)
        if idx < 0:
            break
        print(repr(text[max(0, idx - 150) : idx + 250]))
        idx += len(needle)
        n += 1

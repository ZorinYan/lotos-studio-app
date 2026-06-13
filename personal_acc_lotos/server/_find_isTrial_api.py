import re
import requests

base = "https://n1996926.yclients.com/"
main = requests.get(base + "main-TSJIUNFL.js", timeout=60).text
chunks = sorted(set(re.findall(r'import\("\./([^"]+\.js)"\)', main)))

needles = [
    "getIsTrialVisitActivated",
    "isTrialVisit",
    "is_trial_visit",
    "isTrial:",
    "is_trial:",
    "updateVisitTypeForActivity",
]

for chunk in [""] + chunks:
    url = base + (chunk or "main-TSJIUNFL.js")
    text = requests.get(url, timeout=60).text
    hits = [n for n in needles if n in text]
    if hits:
        print("FILE", chunk or "main", hits)
        for n in hits:
            idx = 0
            c = 0
            while c < 3:
                idx = text.find(n, idx)
                if idx < 0:
                    break
                print(" ", n, repr(text[max(0, idx - 100) : idx + 180]))
                idx += len(n)
                c += 1

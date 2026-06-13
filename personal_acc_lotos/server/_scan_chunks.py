import re
import requests

base = "https://n1996926.yclients.com/"
main = requests.get(base + "main-TSJIUNFL.js", timeout=60).text
chunks = sorted(set(re.findall(r'import\("\./([^"]+\.js)"\)', main)))
print("chunks", len(chunks), chunks[:20])

needles = ["trial_settings", "is_trial", "trial_visit", "isTrial", "salon_service_id", "пробное", "trialSettings", "isTrialVisit"]

for chunk in chunks:
    url = base + chunk
    try:
        text = requests.get(url, timeout=60).text
    except requests.RequestException as error:
        print(chunk, "ERR", error)
        continue
    hits = [n for n in needles if n.lower() in text.lower()]
    if hits:
        print("HIT", chunk, len(text), hits)
        for n in hits[:2]:
            idx = text.lower().find(n.lower())
            print(" ", repr(text[max(0, idx - 100) : idx + 150]))

import re
import requests

text = requests.get("https://n1996926.yclients.com/main-TSJIUNFL.js", timeout=60).text

for needle in ["attendances", "trial_settings", "is_trial", "trial_visit", "isTrial", "service_trial", "salon_service"]:
    idx = 0
    found = 0
    while found < 3:
        idx = text.find(needle, idx)
        if idx < 0:
            break
        print(f"=== {needle} @ {idx}")
        print(repr(text[max(0, idx - 120) : idx + 200]))
        idx += len(needle)
        found += 1

# search split trial word parts
for m in re.finditer(r"Trial[A-Za-z]*", text):
    if m.group() not in ("Trial",):
        print("TrialWord", m.group(), repr(text[m.start() : m.start() + 80]))

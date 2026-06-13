import re
import requests

base = "https://n1996926.yclients.com/"
html = requests.get(base, timeout=30).text
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print("scripts", scripts)

needles = ["trial_settings", "is_trial", "trial_visit", "isTrial", "salon_service_id", "пробное"]

for script in scripts:
    url = script if script.startswith("http") else base.rstrip("/") + script
    if not url.startswith("http"):
        url = base + script.lstrip("/")
    text = requests.get(url, timeout=60).text
    hits = []
    for n in needles:
        if n.lower() in text.lower():
            hits.append(n)
    print(url, len(text), hits)
    if hits:
        for n in hits:
            idx = text.lower().find(n.lower())
            print(" ", repr(text[max(0, idx - 80) : idx + 120]))

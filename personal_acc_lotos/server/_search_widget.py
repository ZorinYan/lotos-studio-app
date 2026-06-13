import requests

url = "https://widgetv3.yclients.com/widgetJS.js"
text = requests.get(url, timeout=60).text
print("size", len(text))

needles = [
    "trial",
    "is_trial",
    "trial_visit",
    "trial_settings",
    "salon_service_id",
    "isTrial",
    "trialVisit",
    "пробное",
    "пробн",
    "is_trial_visit",
    "service_trial",
]

for needle in needles:
    count = text.lower().count(needle.lower())
    if count:
        idx = text.lower().find(needle.lower())
        print(needle, count, repr(text[max(0, idx - 50) : idx + 100]))

# activity book endpoint patterns
import re

for pat in [r"activity/\$\{[^}]+\}/book", r"/activity/[^\"']+/book", r"is_trial[a-z_]*"]:
    matches = re.findall(pat, text, flags=re.I)
    if matches:
        print("PAT", pat, matches[:5])

import re
import requests

url = "https://n1996926.yclients.com/main-TSJIUNFL.js"
response = requests.get(url, timeout=60)
text = response.text
print("size", len(text))

patterns = [
    "trial",
    "is_trial",
    "trial_visit",
    "trial_settings",
    "salon_service_id",
    "service_trial",
    "isTrial",
    "trialVisit",
    "пробн",
]

for pattern in patterns:
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    print(pattern, len(matches))
    for match in matches[:3]:
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 80)
        print(" ", repr(text[start:end]))

# find activity book endpoint usage
for pat in ["/activity/", "/book", "salon_service"]:
    print(pat, text.count(pat))

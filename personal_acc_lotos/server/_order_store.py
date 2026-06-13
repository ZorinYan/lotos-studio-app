import re
import requests

text = requests.get("https://n1996926.yclients.com/main-TSJIUNFL.js", timeout=60).text

for needle in [
    "getIsTrialVisitActivated",
    "SetTrialVisit",
    "isTrialVisit",
    "is_trial_visit",
    "trial_visit",
    "VISIT_TYPE",
    "VisitType",
]:
    if needle in text:
        idx = text.find(needle)
        print(needle, repr(text[max(0, idx - 80) : idx + 200]))

# search order-confirmation chunk
text2 = requests.get(
    "https://n1996926.yclients.com/order-confirmation.module-VNSI3UTR.js", timeout=60
).text
for needle in ["isTrial", "is_trial", "book_record", "attendances", "trial"]:
    if needle.lower() in text2.lower():
        idx = text2.lower().find(needle.lower())
        print("order-conf", needle, repr(text2[max(0, idx - 100) : idx + 200]))

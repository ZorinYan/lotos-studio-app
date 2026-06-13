import re
import requests

base = "https://n1996926.yclients.com/"
text = requests.get(base + "chunk-43DN4EEI.js", timeout=60).text
print("len", len(text))
needles = [
    "isTrial",
    "is_trial",
    "isTrialVisit",
    "is_trial_visit",
    "book_record",
    "activity/",
    "/book",
    "SetTrial",
    "trial_visit",
    "getIsTrialVisitActivated",
    "salon_service",
]
for n in needles:
    c = text.count(n)
    if c:
        print(n, c)

for n in ["isTrialVisit", "is_trial_visit", "isTrial:", "book_record", "activity/"]:
    idx = 0
    shown = 0
    while shown < 5:
        idx = text.find(n, idx)
        if idx < 0:
            break
        print("---", n)
        print(repr(text[max(0, idx - 120) : idx + 200]))
        idx += len(n)
        shown += 1

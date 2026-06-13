import requests

text = requests.get(
    "https://n1996926.yclients.com/activity-flow-HJGZAQ2Q.js", timeout=60
).text

needle = "updateVisitTypeForActivity"
idx = text.find(needle)
print(repr(text[idx : idx + 1200]))

needle2 = "VisitType"
idx2 = text.find(needle2)
print("--- VisitType enum area ---")
print(repr(text[idx2 : idx2 + 400]))

for n in ["isTrial", "is_trial", "trial_activity", "visit_type", "visitType"]:
    i = text.find(n)
    if i >= 0:
        print(n, repr(text[i : i + 200]))

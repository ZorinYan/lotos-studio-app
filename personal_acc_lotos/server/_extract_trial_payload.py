import re
import requests

base = "https://n1996926.yclients.com/"
for chunk in ["activity-flow-HJGZAQ2Q.js", "booking-flow-DZZ6U7KR.js"]:
    text = requests.get(base + chunk, timeout=60).text
    print("===", chunk, len(text))
    for needle in [
        "isTrial",
        "is_trial",
        "isTrialVisit",
        "VisitType",
        "book_record",
        "attendances",
        "salon_service",
        "trial_settings",
    ]:
        count = text.count(needle)
        if count:
            print(needle, count)
    print()
    for m in re.finditer(r".{0,80}isTrial.{0,120}", text):
        print(m.group()[:200])
        break
    for m in re.finditer(r".{0,80}book_record.{0,120}", text):
        print(m.group()[:200])
    for m in re.finditer(r".{0,80}attendances.{0,120}", text):
        print(m.group()[:200])

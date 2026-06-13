import re
import requests

text = requests.get(
    "https://n1996926.yclients.com/chunk-43DN4EEI.js", timeout=60
).text

for needle in ["createActivity", "is_trial", "trial_visit"]:
    idx = 0
    shown = 0
    while shown < 8:
        idx = text.find(needle, idx)
        if idx < 0:
            break
        print("===", needle, idx)
        print(text[max(0, idx - 80) : idx + 350])
        print()
        idx += len(needle)
        shown += 1

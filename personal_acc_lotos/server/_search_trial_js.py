import re
import requests

PATTERNS = [
    "trial",
    "is_trial",
    "trial_visit",
    "trial_settings",
    "salon_service_id",
    "service_trial",
]

URLS = [
    "https://n1996926.yclients.com/",
    "https://widgetv3.yclients.com/widgetJS.js",
    "https://assets.yclients.com/booking-widget/booking-widget.js",
]

for url in URLS:
    try:
        response = requests.get(url, timeout=30)
    except requests.RequestException as error:
        print(url, "ERR", error)
        continue
    text = response.text
    print("===", url, response.status_code, len(text))
    for pattern in PATTERNS:
        count = len(re.findall(pattern, text, flags=re.IGNORECASE))
        if count:
            print(" ", pattern, count)
    if url.endswith("/"):
        scripts = re.findall(r'src="([^"]+\.js[^"]*)"', text)
        print(" scripts", scripts[:10])

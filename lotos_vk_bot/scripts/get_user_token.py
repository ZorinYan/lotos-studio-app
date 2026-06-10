"""
Получить YCLIENTS_USER_TOKEN для .env.

Запуск:
    python scripts/get_user_token.py

Нужны переменные в .env:
    YCLIENTS_PARTNER_TOKEN
    YCLIENTS_LOGIN
    YCLIENTS_PASSWORD
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

PARTNER_TOKEN = os.getenv("YCLIENTS_PARTNER_TOKEN", "")
LOGIN = os.getenv("YCLIENTS_LOGIN", "")
PASSWORD = os.getenv("YCLIENTS_PASSWORD", "")


def main() -> int:
    if not PARTNER_TOKEN or not LOGIN or not PASSWORD:
        print("Добавьте в .env: YCLIENTS_PARTNER_TOKEN, YCLIENTS_LOGIN, YCLIENTS_PASSWORD")
        return 1

    response = requests.post(
        "https://api.yclients.com/api/v1/auth",
        headers={
            "Authorization": f"Bearer {PARTNER_TOKEN}",
            "Accept": "application/vnd.yclients.v2+json",
            "Content-Type": "application/json",
        },
        json={"login": LOGIN, "password": PASSWORD},
        timeout=15,
    )

    if response.status_code not in (200, 201):
        print(f"Ошибка {response.status_code}: {response.text}")
        return 1

    payload = response.json()
    user_token = payload.get("data", {}).get("user_token") or payload.get("user_token")

    if not user_token:
        print("Токен не найден в ответе. Возможно, включена 2FA:")
        print(response.text)
        return 1

    print("Скопируйте в .env:")
    print(f"YCLIENTS_USER_TOKEN={user_token}")
    print()
    print("Затем проверьте права:")
    print("  python scripts/check_permissions.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

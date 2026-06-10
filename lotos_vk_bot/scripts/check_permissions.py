"""
Проверить, хватает ли прав у YCLIENTS_USER_TOKEN для работы бота.

Запуск:
    python scripts/check_permissions.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import load_config
from yclients import YClientsClient, YClientsError


def main() -> int:
    try:
        config = load_config()
        client = YClientsClient(config)
        permissions = client.get_permissions()
    except YClientsError as error:
        print(error)
        return 1

    loyalty = permissions.get("loyalty", {})
    clients = permissions.get("clients", {})

    loyalty_ok = bool(
        loyalty.get("loyalty_access") or loyalty.get("has_loyalty_access")
    )
    clients_ok = bool(clients.get("clients_access"))
    phones_ok = bool(clients.get("client_phones_access"))
    records_ok = bool(permissions.get("record_form", {}).get("record_form_access"))

    print(f"Филиал (company_id): {config.yclients_company_id}")
    print()
    print(f"  Лояльность (абонементы):     {'ДА' if loyalty_ok else 'НЕТ'}")
    print(f"  Клиентская база (кабинет): {'ДА' if clients_ok else 'НЕТ'}")
    print(f"  Телефоны клиентов:           {'ДА' if phones_ok else 'НЕТ'}")
    print(f"  Записи (ближайшие визиты):   {'ДА' if records_ok else 'НЕТ'}")
    print()

    missing = []
    if not loyalty_ok:
        missing.append("Лояльность")
    if not clients_ok:
        missing.append("Клиентская база")
    if not phones_ok:
        missing.append("Телефоны клиентов")

    if not missing:
        print("Права в порядке — бот может работать с абонементами и личным кабинетом.")
        return 0

    print("Не хватает прав:", ", ".join(missing))
    print("Включите их в YClients → Сотрудники → Права доступа")
    print("Затем заново получите токен: python scripts/get_user_token.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())

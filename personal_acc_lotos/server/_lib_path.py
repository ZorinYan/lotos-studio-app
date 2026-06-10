"""Добавляет в sys.path общий код YClients (бот / server/lib)."""

import sys
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent
_LIB_CANDIDATES = (
    _SERVER_DIR / "lib",
    _SERVER_DIR.parent.parent / "lotos_vk_bot",
)

_configured = False


def ensure_lib_path() -> None:
    global _configured
    if _configured:
        return

    for root in _LIB_CANDIDATES:
        if root.is_dir():
            path = str(root)
            if path not in sys.path:
                # В конец path: иначе lotos_vk_bot/main.py перекрывает server/main.py
                sys.path.append(path)
            _configured = True
            return

    raise RuntimeError(
        "Не найдена общая библиотека. Ожидается personal_acc_lotos/server/lib "
        "или lotos_vk_bot в корне репозитория."
    )

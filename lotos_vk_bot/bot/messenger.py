import random
from contextlib import contextmanager
from typing import Generator


class Messenger:
    def __init__(self, vk) -> None:
        self.vk = vk

    def send_message(
        self,
        user_id: int,
        text: str,
        keyboard: str | None = None,
    ) -> int | None:
        params = {
            "user_id": user_id,
            "message": text,
            "random_id": random.randint(1, 2**31 - 1),
        }
        if keyboard:
            params["keyboard"] = keyboard
        try:
            return int(self.vk.messages.send(**params))
        except (TypeError, ValueError):
            return None

    def delete_message(self, user_id: int, message_id: int | None) -> None:
        if not message_id:
            return
        try:
            self.vk.messages.delete(
                message_ids=message_id,
                delete_for_all=1,
                peer_id=user_id,
            )
        except Exception:
            pass

    @contextmanager
    def loading(
        self,
        user_id: int,
        text: str,
        keyboard: str | None = None,
    ) -> Generator[None, None, None]:
        message_id = self.send_message(user_id, text, keyboard)
        try:
            yield
        finally:
            self.delete_message(user_id, message_id)

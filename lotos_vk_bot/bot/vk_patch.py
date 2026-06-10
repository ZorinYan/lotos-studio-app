"""
Патч vk_api: некоторые события (стикер, фото, MESSAGE_EDIT) приходят без text.
"""


def apply() -> None:
    from vk_api.longpoll import Event

    original = Event._parse_message

    def safe_parse_message(self):
        if not hasattr(self, "text") or self.text is None:
            self.text = ""
        return original(self)

    Event._parse_message = safe_parse_message

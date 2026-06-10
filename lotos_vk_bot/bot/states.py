AWAITING_PHONE = "awaiting_phone"
AWAITING_CLIENT_NAME = "awaiting_client_name"
ADMIN_CHAT = "admin_chat"

PURPOSE_ABONEMENT = "abonement"
PURPOSE_CABINET = "cabinet"
PURPOSE_LOGIN = "login"
PURPOSE_NEXT_RECORD = "next_record"
PURPOSE_LINK = "link"
PURPOSE_BOOKING = "booking"
PURPOSE_CANCEL_RECORD = "cancel_record"

_user_states: dict[int, str] = {}
_pending_actions: dict[int, str] = {}
_pending_phones: dict[int, str] = {}


def set_state(user_id: int, state: str | None) -> None:
    if state is None:
        _user_states.pop(user_id, None)
    else:
        _user_states[user_id] = state


def get_state(user_id: int) -> str | None:
    return _user_states.get(user_id)


def set_pending_action(user_id: int, action: str) -> None:
    _pending_actions[user_id] = action


def get_pending_action(user_id: int) -> str | None:
    return _pending_actions.get(user_id)


def pop_pending_action(user_id: int) -> str | None:
    return _pending_actions.pop(user_id, None)


def set_pending_phone(user_id: int, phone: str) -> None:
    _pending_phones[user_id] = phone


def get_pending_phone(user_id: int) -> str | None:
    return _pending_phones.get(user_id)


def pop_pending_phone(user_id: int) -> str | None:
    return _pending_phones.pop(user_id, None)


def clear_pending(user_id: int) -> None:
    _pending_actions.pop(user_id, None)
    _pending_phones.pop(user_id, None)

def normalize_name_part(value: str) -> str:
    return " ".join(value.strip().lower().replace("ё", "е").split())


def client_has_surname(profile: dict) -> bool:
    return bool(normalize_name_part(profile.get("surname") or ""))


def client_names_match(profile: dict, user_input: str) -> bool:
    crm_name = normalize_name_part(profile.get("name") or "")
    crm_surname = normalize_name_part(profile.get("surname") or "")
    user_full = normalize_name_part(user_input)

    if not crm_name or not user_full:
        return False

    if not crm_surname:
        if user_full == crm_name:
            return True
        return user_full.split()[0] == crm_name

    parts = user_full.split()
    if len(parts) < 2:
        return False

    user_name = parts[0]
    user_surname = " ".join(parts[1:])
    return user_name == crm_name and user_surname == crm_surname

from bot import messages
from bot.keyboards import cabinet_menu, main_menu, schedule_period_menu
from bot.messenger import Messenger
from utils import user_prefs
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters_trainer import format_favorite_staff


class TrainerHandler:
    def __init__(self, yclients: YClientsClient, messenger: Messenger) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self._pick_maps: dict[int, dict[str, int]] = {}

    def show_favorite(self, user_id: int) -> None:
        favorite = user_prefs.get_favorite_staff(user_id)
        self.messenger.send_message(
            user_id,
            format_favorite_staff(favorite),
            cabinet_menu(),
        )

    def start_pick(self, user_id: int) -> None:
        try:
            with self.messenger.loading(user_id, messages.loading_trainers(), cabinet_menu()):
                trainers = self.yclients.collect_staff_from_activities(14)
        except YClientsPermissionError:
            self.messenger.send_message(
                user_id, messages.service_unavailable(), cabinet_menu()
            )
            return
        except YClientsError as error:
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), cabinet_menu()
            )
            return

        if not trainers:
            self.messenger.send_message(
                user_id, messages.no_trainers_for_pick(), cabinet_menu()
            )
            return

        from bot.trainer_keyboards import build_trainer_pick_keyboard

        label_map: dict[str, int] = {}
        labels: list[str] = []
        used: set[str] = set()
        for trainer in trainers:
            name = trainer["name"]
            label = name
            if label in used:
                label = f"{name} ({trainer['id']})"
            used.add(label)
            label_map[label] = trainer["id"]
            labels.append(label)

        self._pick_maps[user_id] = label_map
        self.messenger.send_message(
            user_id,
            messages.choose_favorite_trainer(),
            build_trainer_pick_keyboard(labels),
        )

    def handle_pick(self, user_id: int, text: str) -> bool:
        label_map = self._pick_maps.get(user_id)
        if not label_map:
            return False

        if text == "Убрать избранного":
            user_prefs.clear_favorite_staff(user_id)
            self._pick_maps.pop(user_id, None)
            self.messenger.send_message(
                user_id,
                messages.favorite_trainer_cleared(),
                cabinet_menu(),
            )
            return True

        staff_id = label_map.get(text)
        if not staff_id:
            return False

        user_prefs.set_favorite_staff(user_id, staff_id, text.split(" (")[0])
        self._pick_maps.pop(user_id, None)
        self.messenger.send_message(
            user_id,
            messages.favorite_trainer_saved(text.split(" (")[0]),
            cabinet_menu(),
        )
        return True

    def is_picking(self, user_id: int) -> bool:
        return user_id in self._pick_maps

    def cancel_pick(self, user_id: int) -> None:
        self._pick_maps.pop(user_id, None)

    def show_schedule_for_favorite(self, user_id: int, *, days: int = 7) -> None:
        favorite = user_prefs.get_favorite_staff(user_id)
        if not favorite:
            self.messenger.send_message(
                user_id,
                messages.favorite_trainer_not_set(),
                schedule_period_menu(user_id),
            )
            return

        loading_text = messages.loading_schedule_trainer(favorite["name"], days)
        try:
            with self.messenger.loading(user_id, loading_text, schedule_period_menu(user_id)):
                activities = self.yclients.get_schedule_activities(days)
                activities = self.yclients.filter_activities_by_staff(
                    activities, favorite["id"]
                )
        except YClientsPermissionError:
            self.messenger.send_message(
                user_id, messages.service_unavailable(), main_menu(user_id)
            )
            return
        except YClientsError as error:
            self.messenger.send_message(
                user_id, messages.fetch_error(str(error)), main_menu(user_id)
            )
            return

        from yclients.formatters_schedule import format_schedule

        title = f"Мой тренер · {favorite['name']}"
        parts = format_schedule(activities, days, title=title)
        for index, part in enumerate(parts):
            keyboard = (
                main_menu(user_id)
                if index == len(parts) - 1
                else schedule_period_menu(user_id)
            )
            self.messenger.send_message(user_id, part, keyboard)

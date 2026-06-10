from datetime import date
from typing import Callable

from bot import booking_context, messages
from bot.booking_context import BookingContext
from bot.booking_keyboards import (
    BTN_ANY_STAFF,
    BTN_CONFIRM_NO,
    BTN_CONFIRM_YES,
    BTN_PAGE_NEXT,
    BTN_PAGE_PREV,
    CLASS_PAGE_SIZE,
    DAY_PAGE_SIZE,
    STAFF_PAGE_SIZE,
    build_class_keyboard,
    build_confirm_keyboard,
    build_day_keyboard,
    build_staff_keyboard,
    make_day_map,
    page_caption,
)
from bot.keyboards import main_menu
from bot.messenger import Messenger
from config import Config
from utils import user_prefs
from utils.phone import format_phone_display
from utils.text_style import spots_line
from yclients import YClientsClient, YClientsError, YClientsPermissionError
from yclients.formatters_booking import format_activity_card, format_booking_success

MAX_CLASS_LABEL = 40


class BookingHandler:
    def __init__(
        self,
        yclients: YClientsClient,
        messenger: Messenger,
        config: Config,
        get_first_name: Callable[[int], str | None],
    ) -> None:
        self.yclients = yclients
        self.messenger = messenger
        self.config = config
        self.get_first_name = get_first_name

    def cancel(self, user_id: int) -> None:
        booking_context.clear(user_id)

    def open(self, user_id: int, phone: str | None) -> None:
        if not phone:
            return
        self._load_days(user_id, phone)

    def open_book_again(self, user_id: int, phone: str | None) -> None:
        if not phone:
            return

        prefs = user_prefs.get_last_booking(user_id)
        if not prefs:
            prefs = self._infer_last_booking_from_visits(user_id, phone)
        if not prefs:
            self.messenger.send_message(
                user_id, messages.book_again_unavailable(), main_menu(user_id)
            )
            return

        try:
            with self.messenger.loading(user_id, messages.loading_booking(), main_menu(user_id)):
                activities = self.yclients.get_bookable_activities(14)
        except YClientsPermissionError:
            self.messenger.send_message(user_id, messages.service_unavailable(), main_menu(user_id))
            return
        except YClientsError as error:
            self.messenger.send_message(user_id, messages.fetch_error(str(error)), main_menu(user_id))
            return

        matched = self.yclients.filter_activities_like_booking(
            activities,
            staff_id=prefs["staff_id"],
            service_title=prefs["service_title"],
            service_id=prefs.get("service_id"),
        )
        if not matched:
            self.messenger.send_message(
                user_id,
                messages.book_again_no_slots(prefs["staff_name"], prefs["service_title"]),
                main_menu(user_id),
            )
            return

        ctx = booking_context.start(user_id)
        ctx.mode = "book_again"
        ctx.filtered_activities = matched

        if len(matched) == 1:
            ctx.selected_activity = matched[0]
            ctx.step = "confirm"
            self.messenger.send_message(
                user_id,
                messages.booking_confirm(format_activity_card(matched[0])),
                build_confirm_keyboard(),
            )
            return

        ctx.class_map, ctx.class_labels = self._build_class_map(matched, with_trainer=False)
        ctx.class_page = 0
        ctx.step = "class"
        self.messenger.send_message(
            user_id,
            messages.book_again_choose() + page_caption(0, len(ctx.class_labels), CLASS_PAGE_SIZE),
            build_class_keyboard(ctx.class_labels, 0),
        )

    def handle_message(self, user_id: int, text: str, phone: str | None) -> bool:
        ctx = booking_context.get(user_id)
        if not ctx:
            return False

        if text == BTN_CONFIRM_NO:
            self.cancel(user_id)
            self.messenger.send_message(user_id, messages.booking_cancelled(), main_menu(user_id))
            return True

        if text in {BTN_PAGE_NEXT, BTN_PAGE_PREV}:
            return self._handle_page(user_id, text)

        if ctx.step == "day":
            return self._handle_day(user_id, text)
        if ctx.step == "staff":
            return self._handle_staff(user_id, text)
        if ctx.step == "class":
            return self._handle_class(user_id, text)
        if ctx.step == "confirm":
            return self._handle_confirm(user_id, text, phone)

        return False

    def _handle_page(self, user_id: int, text: str) -> bool:
        ctx = booking_context.get(user_id)
        if not ctx:
            return False

        delta = 1 if text == BTN_PAGE_NEXT else -1
        if ctx.step == "day":
            ctx.day_page = self._clamp_page(
                ctx.day_page + delta, len(ctx.day_labels), DAY_PAGE_SIZE
            )
            self._show_day_keyboard(user_id, ctx)
            return True
        if ctx.step == "staff":
            ctx.staff_page = self._clamp_page(
                ctx.staff_page + delta, len(ctx.staff_names), STAFF_PAGE_SIZE
            )
            self._show_staff_keyboard(user_id, ctx)
            return True
        if ctx.step == "class":
            ctx.class_page = self._clamp_page(
                ctx.class_page + delta, len(ctx.class_labels), CLASS_PAGE_SIZE
            )
            self._show_class_keyboard(user_id, ctx)
            return True
        return False

    @staticmethod
    def _clamp_page(page: int, total: int, page_size: int) -> int:
        if total <= 0:
            return 0
        max_page = (total + page_size - 1) // page_size - 1
        return max(0, min(page, max_page))

    def _load_days(self, user_id: int, phone: str) -> None:
        ctx = booking_context.start(user_id)
        ctx.step = "day"
        try:
            with self.messenger.loading(user_id, messages.loading_booking(), main_menu(user_id)):
                ctx.all_activities = self.yclients.get_bookable_activities(14)
        except YClientsPermissionError:
            booking_context.clear(user_id)
            self.messenger.send_message(user_id, messages.service_unavailable(), main_menu(user_id))
            return
        except YClientsError as error:
            booking_context.clear(user_id)
            self.messenger.send_message(user_id, messages.fetch_error(str(error)), main_menu(user_id))
            return

        dates = self._unique_dates(ctx.all_activities)
        if not dates:
            booking_context.clear(user_id)
            self.messenger.send_message(user_id, messages.booking_no_slots(), main_menu(user_id))
            return

        ctx.day_map = make_day_map(dates)
        ctx.day_labels = list(ctx.day_map.keys())
        ctx.day_page = 0
        self._show_day_keyboard(user_id, ctx)

    def _show_day_keyboard(self, user_id: int, ctx: BookingContext) -> None:
        caption = page_caption(ctx.day_page, len(ctx.day_labels), DAY_PAGE_SIZE)
        self.messenger.send_message(
            user_id,
            messages.booking_choose_day() + caption,
            build_day_keyboard(ctx.day_labels, ctx.day_page),
        )

    def _show_staff_keyboard(self, user_id: int, ctx: BookingContext) -> None:
        assert ctx.selected_date is not None
        caption = page_caption(ctx.staff_page, len(ctx.staff_names), STAFF_PAGE_SIZE)
        self.messenger.send_message(
            user_id,
            messages.booking_choose_staff(ctx.selected_date) + caption,
            build_staff_keyboard(ctx.staff_names, ctx.staff_page),
        )

    def _show_class_keyboard(self, user_id: int, ctx: BookingContext) -> None:
        caption = page_caption(ctx.class_page, len(ctx.class_labels), CLASS_PAGE_SIZE)
        self.messenger.send_message(
            user_id,
            messages.booking_choose_class() + caption,
            build_class_keyboard(ctx.class_labels, ctx.class_page),
        )

    def _handle_day(self, user_id: int, text: str) -> bool:
        ctx = booking_context.get(user_id)
        if not ctx:
            return False

        selected = ctx.day_map.get(text)
        if not selected:
            return False

        ctx.selected_date = selected
        ctx.day_activities = self._activities_for_day(ctx.all_activities, selected)
        if not ctx.day_activities:
            self.messenger.send_message(
                user_id,
                messages.booking_day_empty(),
                build_day_keyboard(ctx.day_labels, ctx.day_page),
            )
            return True

        ctx.staff_names, ctx.staff_map = self._collect_staff(ctx.day_activities)
        ctx.staff_page = 0
        ctx.step = "staff"
        self._show_staff_keyboard(user_id, ctx)
        return True

    def _handle_staff(self, user_id: int, text: str) -> bool:
        ctx = booking_context.get(user_id)
        if not ctx:
            return False

        if text == BTN_ANY_STAFF:
            ctx.selected_staff_id = None
        elif text in ctx.staff_map:
            ctx.selected_staff_id = ctx.staff_map[text]
        else:
            return False

        filtered = self._filter_by_staff(ctx.day_activities, ctx.selected_staff_id)
        if not filtered:
            ctx.step = "staff"
            self.messenger.send_message(
                user_id,
                messages.booking_no_classes_for_staff(),
                build_staff_keyboard(ctx.staff_names, ctx.staff_page),
            )
            return True

        ctx.filtered_activities = filtered
        with_trainer = ctx.selected_staff_id is None
        ctx.class_map, ctx.class_labels = self._build_class_map(filtered, with_trainer)
        ctx.class_page = 0
        ctx.step = "class"
        self._show_class_keyboard(user_id, ctx)
        return True

    def _handle_class(self, user_id: int, text: str) -> bool:
        ctx = booking_context.get(user_id)
        if not ctx:
            return False

        activity_id = ctx.class_map.get(text)
        if not activity_id:
            return False

        activity = next(
            (item for item in ctx.filtered_activities if item.get("id") == activity_id),
            None,
        )
        if not activity:
            return False

        ctx.selected_activity = activity
        ctx.step = "confirm"
        self.messenger.send_message(
            user_id,
            messages.booking_confirm(format_activity_card(activity)),
            build_confirm_keyboard(),
        )
        return True

    def _handle_confirm(self, user_id: int, text: str, phone: str | None) -> bool:
        if text != BTN_CONFIRM_YES:
            return False

        ctx = booking_context.get(user_id)
        if not ctx or not ctx.selected_activity or not phone:
            return False

        activity = ctx.selected_activity
        activity_id = activity.get("id")
        if not activity_id:
            booking_context.clear(user_id)
            self.messenger.send_message(user_id, messages.booking_failed("Нет ID занятия"), main_menu(user_id))
            return True

        fullname, surname = self._resolve_fullname(user_id, phone)
        display = format_phone_display(phone)

        try:
            with self.messenger.loading(user_id, messages.loading_booking_submit(), main_menu(user_id)):
                self.yclients.book_activity(
                    activity_id,
                    phone,
                    fullname,
                    surname,
                )
        except YClientsError as error:
            booking_context.clear(user_id)
            self.messenger.send_message(user_id, messages.booking_failed(str(error)), main_menu(user_id))
            return True

        staff = activity.get("staff", {})
        service = activity.get("service", {})
        staff_id = staff.get("id")
        service_title = self.yclients.activity_service_title(activity)
        if staff_id:
            user_prefs.set_last_booking(
                user_id,
                staff_id=int(staff_id),
                staff_name=(staff.get("name") or staff.get("specialization") or "Тренер").strip(),
                service_title=service_title,
                service_id=service.get("id"),
            )

        booking_context.clear(user_id)
        self.messenger.send_message(
            user_id,
            format_booking_success(activity, display),
            main_menu(user_id),
        )
        return True

    @staticmethod
    def _unique_dates(activities: list[dict]) -> list[date]:
        dates: set[date] = set()
        for activity in activities:
            dt = YClientsClient._parse_activity_datetime(activity)
            if dt:
                dates.add(dt.date())
        return sorted(dates)

    @staticmethod
    def _activities_for_day(activities: list[dict], day: date) -> list[dict]:
        result = []
        for activity in activities:
            dt = YClientsClient._parse_activity_datetime(activity)
            if dt and dt.date() == day:
                result.append(activity)
        result.sort(key=lambda item: YClientsClient._parse_activity_datetime(item) or day)
        return result

    @staticmethod
    def _collect_staff(activities: list[dict]) -> tuple[list[str], dict[str, int]]:
        staff_map: dict[str, int] = {}
        for activity in activities:
            staff = activity.get("staff", {})
            staff_id = staff.get("id")
            name = (staff.get("name") or staff.get("specialization") or "Тренер").strip()
            if not staff_id:
                continue
            if name in staff_map and staff_map[name] != staff_id:
                name = f"{name} ({staff_id})"
            staff_map[name] = staff_id
        return sorted(staff_map.keys()), staff_map

    @staticmethod
    def _filter_by_staff(activities: list[dict], staff_id: int | None) -> list[dict]:
        if staff_id is None:
            return list(activities)
        return [
            item
            for item in activities
            if item.get("staff", {}).get("id") == staff_id
        ]

    @staticmethod
    def _build_class_map(
        activities: list[dict], with_trainer: bool
    ) -> tuple[dict[str, int], list[str]]:
        class_map: dict[str, int] = {}
        labels: list[str] = []
        used: set[str] = set()
        for activity in activities:
            activity_id = activity.get("id")
            if not activity_id:
                continue
            label = BookingHandler._class_label(activity, with_trainer=with_trainer)
            if label in used:
                label = f"{label[:36]} ({activity_id})"[:MAX_CLASS_LABEL]
            used.add(label)
            class_map[label] = activity_id
            labels.append(label)
        return class_map, labels

    @staticmethod
    def _class_label(activity: dict, *, with_trainer: bool) -> str:
        dt = YClientsClient._parse_activity_datetime(activity)
        service = activity.get("service", {})
        title = service.get("title", "Занятие")
        time_str = dt.strftime("%H:%M") if dt else "—"
        label = f"{time_str} · {title}"
        if with_trainer:
            staff = activity.get("staff", {})
            trainer = (staff.get("name") or staff.get("specialization") or "").strip()
            if trainer:
                first_name = trainer.split()[0]
                suffix = f" · {first_name}"
                if len(label) + len(suffix) <= MAX_CLASS_LABEL:
                    label += suffix
        spots = spots_line(activity.get("capacity") or 0, activity.get("records_count") or 0)
        if spots:
            short = spots.replace("🟢  свободно ", "").replace("🔴  ", "")
            suffix = f" · {short}"
            if len(label) + len(suffix) <= MAX_CLASS_LABEL:
                label += suffix
        return label[:MAX_CLASS_LABEL]

    def _infer_last_booking_from_visits(self, user_id: int, phone: str) -> dict | None:
        try:
            visits = self.yclients.get_recent_visits(phone, limit=8)
        except Exception:
            return None

        for visit in visits:
            staff = visit.get("staff", {})
            staff_id = staff.get("id")
            services = visit.get("services") or []
            if not staff_id or not services:
                continue
            service = services[0]
            prefs = {
                "staff_id": int(staff_id),
                "staff_name": (staff.get("name") or staff.get("specialization") or "Тренер").strip(),
                "service_title": str(service.get("title") or "Занятие"),
                "service_id": service.get("id"),
            }
            user_prefs.set_last_booking(user_id, **prefs)
            return prefs
        return None

    def _resolve_fullname(self, user_id: int, phone: str) -> tuple[str, str]:
        try:
            client = self.yclients.find_client_by_phone(phone)
            if client:
                name = str(client.get("name", "")).strip()
                surname = str(client.get("surname", "")).strip()
                if name:
                    return name, surname
        except Exception:
            pass
        first = self.get_first_name(user_id) or "Клиент"
        return first, ""

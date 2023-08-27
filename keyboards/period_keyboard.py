from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_period_keyboard() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="Сейчас"),
        KeyboardButton(text="Сегодня"),
        KeyboardButton(text="Завтра")
    )

    builder.row(
        KeyboardButton(text="3 Дня"),
        KeyboardButton(text="7 Дней")
    )

    builder.row(
        KeyboardButton(text="Выйти")
    )

    return builder

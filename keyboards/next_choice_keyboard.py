from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_next_choice_keyboard() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="Новый город"),
        KeyboardButton(text="Новый период")
    )

    builder.row(
        KeyboardButton(text="Выйти")
    )

    return builder

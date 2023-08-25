from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_weather() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Узнать погоду")],
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Нажмите, чтобы узнать погоду"
    )

    return keyboard

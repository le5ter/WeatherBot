from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_period() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="Сейчас"),
            KeyboardButton(text="Завтра"),
            KeyboardButton(text="3 Дня")
        ],
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите промежуток"
    )

    return keyboard

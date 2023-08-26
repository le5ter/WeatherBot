from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_start_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="Начать")
        ],
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Нажмите на кнопку, чтобы начать"
    )

    return keyboard

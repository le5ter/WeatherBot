from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State

router = Router()


class States(StatesGroup):
    getting_city = State()
    checking_city = State()
    getting_period = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Введите ваш город:")
    await state.set_state(States.getting_city)


@router.message(Command("clear"))
async def cmd_clear(message: Message, bot: Bot):
    try:
        for i in range(message.message_id, 0, -1):
            await bot.delete_message(message.from_user.id, i)
    except TelegramBadRequest as ex:
        if ex.message == "Bad Request: message to delete not found":
            print("Все сообщения удалены")


@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext):
    await state.set_state(States.getting_city)

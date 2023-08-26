from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State

from keyboards.weather_keyboard import get_weather_keyboard
from keyboards.period_keyboard import get_period_keyboard

router = Router()


class States(StatesGroup):
    getting_weather = State()
    getting_city = State()
    next_choice = State()
    getting_period = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Чтобы узнать погоду, нажмите на кнопку", reply_markup=get_weather_keyboard())
    await state.set_state(States.getting_weather)


@router.message(States.getting_weather, F.text.lower() == "узнать погоду")
async def right_choice(message: Message, state: FSMContext):
    await message.answer("Введите ваш город:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(States.getting_city)


@router.message(States.getting_weather)
async def wrong_choice(message: Message):
    await message.answer("Так не пойдет, нажмите на кнопку!")


@router.message(States.next_choice, F.text.lower() == "новый город")
async def new_city(message: Message, state: FSMContext):
    await message.answer("Введите новый город:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(States.getting_city)


@router.message(States.next_choice, F.text.lower() == "новый период")
async def new_city(message: Message, state: FSMContext):
    await message.answer("Выберите период", reply_markup=get_period_keyboard())
    await state.set_state(States.getting_period)


@router.message(States.next_choice, F.text.lower() == "выйти")
async def new_city(message: Message, state: FSMContext):
    await message.answer("Чтобы узнать погоду, нажмите на кнопку", reply_markup=get_weather_keyboard())
    await state.set_state(States.getting_weather)


@router.message(States.next_choice)
async def new_city(message: Message, state: FSMContext):
    await message.answer("Так не пойдет, нажмите на кнопку!")


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

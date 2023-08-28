import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, Update
from aiogram.fsm.state import StatesGroup, State

from keyboards.weather_keyboard import get_weather_keyboard
from keyboards.period_keyboard import get_period_keyboard
from keyboards.start_keyboard import get_start_keyboard

router = Router()


class States(StatesGroup):
    getting_weather = State()
    getting_city = State()
    next_choice = State()
    getting_period = State()
    stop_st = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id: float = message.from_user.id
    logging.info(f'[+] Пользователь с id: {user_id} запустил бота')
    await message.answer("Чтобы узнать погоду, нажмите на кнопку", reply_markup=get_weather_keyboard())
    await state.set_state(States.getting_weather)


@router.message(Command("stop"))
async def cmd_stop(message: Message, state: FSMContext):
    await message.answer("Чтобы начать заново, нажмите на кнопку", reply_markup=get_start_keyboard())
    await state.set_state(States.stop_st)


@router.message(States.stop_st, F.text.lower() == "начать")
async def start_again(message: Message, state: FSMContext):
    user_id: float = message.from_user.id
    logging.info(f'[+] Пользователь с id: {user_id} запустил бота заново')
    await message.answer("Чтобы узнать погоду, нажмите на кнопку", reply_markup=get_weather_keyboard())
    await state.set_state(States.getting_weather)


@router.message(States.stop_st)
async def start_again(message: Message):
    await message.answer("Не могу понять ваше сообщение:(. Если вы хотите начать заново, то нажмите на кнопку")


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
    await message.answer("Выберите период", reply_markup=get_period_keyboard().as_markup(resize_keyboard=True))
    await state.set_state(States.getting_period)


@router.message(States.next_choice, F.text.lower() == "выйти")
async def new_city(message: Message, state: FSMContext):
    await message.answer("Чтобы начать заново, нажмите на кнопку", reply_markup=get_start_keyboard())
    await state.set_state(States.stop_st)


@router.message(States.next_choice)
async def new_city(message: Message):
    await message.answer("Так не пойдет, нажмите на кнопку!")


@router.errors()
async def error_handler(update: Update, exception: Exception):
    logging.error(f'Ошибка при обработке запроса {update}: {exception}')

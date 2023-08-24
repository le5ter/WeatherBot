from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from handlers.common import GetInfo

router = Router()


@router.message(GetInfo.getting_city)
async def city_chosen(message: Message, state: FSMContext):
    await state.update_data(chosen_city=message.text)
    user_data = await state.get_data()
    if message.text.isdigit():
        await message.answer("Оййй, что-то пошло не так, введите город еще раз!")
    else:
        await message.answer(f"Город: {user_data['chosen_city']}")

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from handlers.common import GetInfo
import aiohttp
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
router = Router()


url = "https://api.gismeteo.net/v2/search/cities/?query="
headers = {
    "X-Gismeteo-Token": f'{os.getenv("API_TOKEN")}',
    "Accept-Encoding": "gzip"
}


@router.message(GetInfo.getting_city)
async def choosing_city(message: Message, state: FSMContext):
    input_city: str = message.text
    await state.update_data(input_city=input_city)

    if input_city.isdigit():
        await message.answer("Оййй, что-то пошло не так, введите город еще раз!")
    else:
        user_data = await state.get_data()
        await message.answer(f"Город: {user_data['input_city']}")

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url+input_city) as response:
                await message.answer(f"{url+input_city}")
                json_body = await response.json()
                code = int(json_body['meta']['code'])
                if code == 200:
                    try:
                        if json_body["response"]["total"] > 0:
                            city_id: int = json_body["response"]["items"][0]["id"]
                            await state.update_data(city_id=city_id)
                            await message.answer("Выберите промежуток")
                            await state.set_state(GetInfo.getting_period)
                        elif json_body["response"]["total"] == 0:
                            await message.answer("Город не найден, попробуйте еще раз")
                    except KeyError:
                        if json_body["response"]["error"]["code"] == 404:
                            await message.answer("Город не найден, попробуйте еще раз")
                        else:
                            await message.answer("Произошла ошибка. Попробуйте еще раз.")
                else:
                    await message.answer("Ошибка сервера, попробуйте позже.")


@router.message(GetInfo.getting_period)
async def choosing_period(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city: int = user_data['city_id']
    await message.answer(f"{city}")
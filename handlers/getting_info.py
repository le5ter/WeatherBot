from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from handlers.common import GetInfo
import aiohttp
import os
from dotenv import load_dotenv, find_dotenv
import datetime

load_dotenv(find_dotenv())
router = Router()


url = "https://api.gismeteo.net/v2/search/cities/?query="
url2 = "https://api.gismeteo.net/v2/weather/current/"
headers = {
    "X-Gismeteo-Token": f'{os.getenv("API_TOKEN")}',
    "Accept-Encoding": "gzip"
}


wind_dict = {0: "Спокойный",
             1: "Северный",
             2: "Северо-Восточный",
             3: "Восточный",
             4: "Юго-восточный",
             5: "Южный",
             6: "Юго-западный",
             7: "Западный",
             8: "Северо-Западный"}


@router.message(GetInfo.getting_city)
async def choosing_city(message: Message, state: FSMContext):
    input_city: str = message.text
    await state.update_data(input_city=input_city)

    if input_city.isdigit():
        await message.answer("Оййй, что-то пошло не так, введите город еще раз!")
    else:
        user_data = await state.get_data()
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url+input_city) as response:
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
    city_id: int = user_data['city_id']
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
    # 'https://api.gismeteo.net/v2/weather/forecast/4368/?lang=en&days=1'
    if message.text.lower() == "сейчас":
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url2}{city_id}") as response:
                json_body = await response.json()
        city: str = user_data['input_city']
        now = datetime.datetime.now()
        format_time = f'{now:%d-%m-%Y %H:%M}'
        description = json_body['response']['description']['full']
        air_temperature = json_body['response']['temperature']['air']['C']
        water_temperature = json_body['response']['temperature']['water']['C']
        humidity = json_body['response']['humidity']['percent']
        pressure = json_body['response']['pressure']['mm_hg_atm']
        wind_direction = json_body['response']['wind']['direction']['scale_8']
        wind_speed = json_body['response']['wind']['speed']['m_s']

        weather_result = f'{city:^30}\n' \
                  f'{format_time:^30}\n' \
                  f'{description}\n' \
                  f'Температура воздуха: {air_temperature}°C\n' \
                  f'Температура воды: {water_temperature}°C\n' \
                  f'Влажность: {humidity}%\n' \
                  f'Давление: {pressure} мм рт. ст.\n' \
                  f'Ветер: {wind_dict[int(wind_direction)]} {wind_speed} м/с\n' + '*' * 30 +\
                  f'\n\n Информация о погоде взята с сайта [Gismeteo](gismeteo.ru)'
        await message.answer(weather_result, parse_mode="MarkdownV2")

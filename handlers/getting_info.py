from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from dotenv import load_dotenv, find_dotenv
import aiohttp
import os
import datetime

from keyboards.period_keyboard import get_period_keyboard
from keyboards.weather_keyboard import get_weather_keyboard
from handlers.common import States

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


@router.message(States.getting_city)
async def getting_city(message: Message, state: FSMContext):
    input_city: str = message.text
    await state.update_data(input_city=input_city)

    if input_city.isdigit():
        await message.answer("Оййй, что-то пошло не так, введите город еще раз!")
    else:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url + input_city) as response:
                json_body = await response.json()
                code = int(json_body['meta']['code'])
                if code == 200:
                    try:
                        if json_body["response"]["total"] > 0:
                            city_id: int = json_body["response"]["items"][0]["id"]
                            city: str = json_body["response"]["items"][0]["name"]
                            await state.update_data(city_id=city_id)
                            await state.update_data(city_name=city)
                            await state.set_state(States.getting_period)

                            await message.answer("Выберите промежуток", reply_markup=get_period_keyboard())
                        elif json_body["response"]["total"] == 0:
                            await message.answer("Город не найден, попробуйте еще раз")
                    except KeyError:
                        if json_body["response"]["error"]["code"] == 404:
                            await message.answer("Город не найден, попробуйте еще раз")
                        else:
                            await message.answer("Произошла ошибка. Попробуйте еще раз.")
                else:
                    await message.answer("Ошибка сервера, попробуйте позже.")


@router.message(States.getting_period, F.text.lower() == "сейчас")
async def getting_current_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{url2}{city_id}") as response:
            json_body = await response.json()
    city: str = user_data['city_name']
    offset = json_body['response']['date']['time_zone_offset']
    offset /= 60
    tz = datetime.timezone(datetime.timedelta(hours=offset), name='МСК')
    now = datetime.datetime.now(tz=tz)
    format_time = f'{now:%d-%m-%Y %H:%M}'
    description = json_body['response']['description']['full']
    air_temperature = json_body['response']['temperature']['air']['C']
    water_temperature = json_body['response']['temperature']['water']['C']
    humidity = json_body['response']['humidity']['percent']
    pressure = json_body['response']['pressure']['mm_hg_atm']
    wind_direction = json_body['response']['wind']['direction']['scale_8']
    wind_speed = json_body['response']['wind']['speed']['m_s']

    weather_result = f'\U0001F30EГород: {city}\n' \
                     f'\U0001F5D3Дата: {format_time}\n' \
                     f'{description}\n' \
                     f'\U0001F321Температура воздуха: {air_temperature}°C\n' \
                     f'\U0001F30AТемпература воды: {water_temperature}°C\n' \
                     f'\U0001F4A7Влажность: {humidity}%\n' \
                     f'\U0001F5FBДавление: {pressure} мм рт. ст.\n' \
                     f'\U0001F32CВетер: {wind_dict[int(wind_direction)]} {wind_speed} м/с\n\n' \
                     f'Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'
    await state.set_state(States.getting_weather)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Чтобы узнать погоду еще раз, нажмите на кнопку", reply_markup=get_weather_keyboard())

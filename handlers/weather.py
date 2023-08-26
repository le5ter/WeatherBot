from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv, find_dotenv
import aiohttp
import os
import datetime

import data.weather_data as wdata
from keyboards.period_keyboard import get_period_keyboard
from keyboards.next_choice_keyboard import get_next_choice_keyboard
from handlers.common import States

load_dotenv(find_dotenv())
router = Router()

url = "https://api.gismeteo.net/v2/search/cities/?query="
url2 = "https://api.gismeteo.net/v2/weather/current/"
url3 = "https://api.gismeteo.net/v2/weather/forecast/by_day_part/"
url4 = "https://api.gismeteo.net/v2/weather/forecast/"
headers = {
    "X-Gismeteo-Token": f'{os.getenv("API_TOKEN")}',
    "Accept-Encoding": "gzip"
}


def format_data(date: str) -> str:
    year = date[:4]
    month = date[5:7]
    day = date[8:]
    return f'{day}-{month}-{year}'


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

                            await message.answer("Выберите период", reply_markup=get_period_keyboard())
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
                     f'\U0001F32AВетер: {wdata.wind_dict[int(wind_direction)]} {wind_speed} м/с\n\n' \
                     f'Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True))


@router.message(States.getting_period, F.text.lower() == "3 дня")
async def getting_3d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{url3}{city_id}/?&days=3") as response:
            json_body = await response.json()
    city: str = user_data['city_name']

    day1 = "Дата: " + format_data(json_body['response'][0]['date']['local'][:10])
    day2 = "Дата: " + format_data(json_body['response'][4]['date']['local'][:10])
    day3 = "Дата: " + format_data(json_body['response'][8]['date']['local'][:10])

    number = 0
    for i in range(1, 4):
        for j in range(1, 5):
            wdata.weather_dict_3d[i][j]['temperature'] = json_body['response'][number]['temperature']['air']['C']
            wdata.weather_dict_3d[i][j]['wind_direction'] = json_body['response'][number]['wind']['direction'][
                'scale_8']
            wdata.weather_dict_3d[i][j]['wind_speed'] = json_body['response'][number]['wind']['speed']['m_s']
            wdata.weather_dict_3d[i][j]['precipitation_amount'] = json_body['response'][number]['precipitation'][
                'amount']
            wdata.weather_dict_3d[i][j]['humidity'] = json_body['response'][number]['humidity']['percent']
            number += 1

    weather_result = f'Город: {city}\n' \
                     f'{day1:^60}\n' \
                     f'\U0001F311Ночь: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[1][1]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[1][1]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[1][1]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[1][1]["wind_direction"]]} {wdata.weather_dict_3d[1][1]["wind_speed"]} м/с\n' \
                     f'\U0001F316Утро: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[1][2]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[1][2]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[1][2]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[1][2]["wind_direction"]]} {wdata.weather_dict_3d[1][2]["wind_speed"]} м/с\n' \
                     f'\U00002600День: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[1][3]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[1][3]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[1][3]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[1][3]["wind_direction"]]} {wdata.weather_dict_3d[1][3]["wind_speed"]} м/с\n' \
                     f'\U0001F312Вечер: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[1][4]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[1][4]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[1][4]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[1][4]["wind_direction"]]} {wdata.weather_dict_3d[1][4]["wind_speed"]} м/с\n' \
                     f'{day2:^60}\n' \
                     f'\U0001F311Ночь: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[2][1]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[2][1]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[2][1]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[2][1]["wind_direction"]]} {wdata.weather_dict_3d[2][1]["wind_speed"]} м/с\n' \
                     f'\U0001F316Утро: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[2][2]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[2][2]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[2][2]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[2][2]["wind_direction"]]} {wdata.weather_dict_3d[2][2]["wind_speed"]} м/с\n' \
                     f'\U00002600День: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[2][3]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[2][3]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[2][3]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[2][3]["wind_direction"]]} {wdata.weather_dict_3d[2][3]["wind_speed"]} м/с\n' \
                     f'\U0001F312Вечер: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[2][4]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[2][4]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[2][4]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[2][4]["wind_direction"]]} {wdata.weather_dict_3d[2][4]["wind_speed"]} м/с\n' \
                     f'{day3:^60}\n' \
                     f'\U0001F311Ночь: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[3][1]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[3][1]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[3][1]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[3][1]["wind_direction"]]} {wdata.weather_dict_3d[3][1]["wind_speed"]} м/с\n' \
                     f'\U0001F316Утро: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[3][2]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[3][2]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[3][2]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[3][2]["wind_direction"]]} {wdata.weather_dict_3d[3][2]["wind_speed"]} м/с\n' \
                     f'\U00002600День: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[3][3]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[3][3]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[3][3]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[3][3]["wind_direction"]]} {wdata.weather_dict_3d[3][3]["wind_speed"]} м/с\n' \
                     f'\U0001F312Вечер: ' \
                     f'\U0001F321 {wdata.weather_dict_3d[3][4]["temperature"]}°C ' \
                     f'\U0001F327 {wdata.weather_dict_3d[3][4]["precipitation_amount"]} мм ' \
                     f'\U0001F4A7 {wdata.weather_dict_3d[3][4]["humidity"]}%\n' \
                     f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[3][4]["wind_direction"]]} {wdata.weather_dict_3d[3][4]["wind_speed"]} м/с\n' \
                     f'\n Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True))


@router.message(States.getting_period, F.text.lower() == "сегодня")
async def getting_1d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{url4}{city_id}/?days=1") as response:
            json_body = await response.json()
    city: str = user_data['city_name']

    wdata.weather_dict_1d['date'] = format_data(json_body['response'][1]['date']['local'][:10])

    for i in range(1, 9):
        wdata.weather_dict_1d[i]['time'] = json_body['response'][i - 1]['date']['local'][11:16]
        wdata.weather_dict_1d[i]['temperature'] = json_body['response'][i - 1]['temperature']['air']['C']
        wdata.weather_dict_1d[i]['wind_speed'] = json_body['response'][i - 1]['wind']['speed']['m_s']
        wdata.weather_dict_1d[i]['wind_direction'] = json_body['response'][i - 1]['wind']['direction']['scale_8']
        wdata.weather_dict_1d[i]['precipitation_amount'] = json_body['response'][i - 1]['precipitation']['amount']
        wdata.weather_dict_1d[i]['pressure'] = json_body['response'][i - 1]['pressure']['mm_hg_atm']

    weather_result = f'Город: {city}\nДата: {wdata.weather_dict_1d["date"]}\n' \
                     f'{wdata.weather_dict_1d[1]["time"]}: \U0001F321{wdata.weather_dict_1d[1]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[1]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[1]["wind_direction"]]} {wdata.weather_dict_1d[1]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[1]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[2]["time"]}: \U0001F321{wdata.weather_dict_1d[2]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[2]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[2]["wind_direction"]]} {wdata.weather_dict_1d[2]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[2]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[3]["time"]}: \U0001F321{wdata.weather_dict_1d[3]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[3]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[3]["wind_direction"]]} {wdata.weather_dict_1d[3]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[3]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[4]["time"]}: \U0001F321{wdata.weather_dict_1d[4]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[4]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[4]["wind_direction"]]} {wdata.weather_dict_1d[4]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[4]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[5]["time"]}: \U0001F321{wdata.weather_dict_1d[5]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[5]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[5]["wind_direction"]]} {wdata.weather_dict_1d[5]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[5]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[6]["time"]}: \U0001F321{wdata.weather_dict_1d[6]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[6]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[6]["wind_direction"]]} {wdata.weather_dict_1d[6]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[6]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[7]["time"]}: \U0001F321{wdata.weather_dict_1d[7]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[7]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[7]["wind_direction"]]} {wdata.weather_dict_1d[7]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[7]["precipitation_amount"]} мм\n' \
                     f'{wdata.weather_dict_1d[8]["time"]}: \U0001F321{wdata.weather_dict_1d[8]["temperature"]}°C ' \
                     f'\U0001F5FB{wdata.weather_dict_1d[8]["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A{wdata.wind_dict[wdata.weather_dict_1d[8]["wind_direction"]]} {wdata.weather_dict_1d[8]["wind_speed"]} м/с ' \
                     f'\U0001F327 {wdata.weather_dict_1d[8]["precipitation_amount"]} мм\n' \
                     f'\nИнформация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True))


@router.message(States.getting_period)
async def wrong_choice(message: Message, state: FSMContext):
    await message.answer("Так не пойдет, нажмите на кнопку!")

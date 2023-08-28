from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv, find_dotenv
import aiohttp
import os
import logging

import data.weather_data as wdata
import data.smiles as smdata
from keyboards.period_keyboard import get_period_keyboard
from keyboards.next_choice_keyboard import get_next_choice_keyboard
from keyboards.weather_keyboard import get_weather_keyboard
from handlers.common import States

load_dotenv(find_dotenv())
router = Router()

url = "https://api.gismeteo.net/v2/search/cities/?query="
url2 = "https://api.gismeteo.net/v2/weather/current/"
url3 = "https://api.gismeteo.net/v2/weather/forecast/by_day_part/"
url4 = "https://api.gismeteo.net/v2/weather/forecast/"
url5 = "https://api.gismeteo.net/v2/weather/forecast/aggregate/"
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
    user_id: float = message.from_user.id
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
                    logging.info(f'[+] Пользователь с id: {user_id} запросил город успешно')

                    await message.answer("Выберите период", reply_markup=get_period_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите период"))
                elif json_body["response"]["total"] == 0:
                    await message.answer("Город не найден, введите город еще раз")
            except KeyError:
                if json_body["response"]["error"]["code"] == 404:
                    await message.answer("Город не найден, введите город еще раз")
                else:
                    logging.warning(f'[!!!] При запросе города пользователем id: {user_id} произошла ошибка сервера')
                    await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
                    await state.set_state(States.getting_weather)
        else:
            logging.warning(f'[!!!] При запросе города пользователем id: {user_id} произошла ошибка сервера')
            await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
            await state.set_state(States.getting_weather)


@router.message(States.getting_period, F.text.lower() == "сейчас")
async def getting_current_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']
    city: str = user_data['city_name']
    user_id: float = message.from_user.id

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url2}{city_id}") as response:
                json_body = await response.json()
        wdata.weather_dict_now['description'] = json_body['response']['description']['full']
        logging.info(f'[+] Пользователь с id: {user_id} запросил период успешно')
    except Exception as ex:
        await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
        await state.set_state(States.getting_weather)
        logging.warning(f'[!!!] При запросе периода пользователем id: {user_id} произошла ошибка {ex}')

    wdata.weather_dict_now['date'] = format_data(json_body['response']['date']['local'][:10]) + " " + json_body['response']['date']['local'][11:16]
    wdata.weather_dict_now['air_temperature'] = json_body['response']['temperature']['air']['C']
    wdata.weather_dict_now['water_temperature'] = json_body['response']['temperature']['water']['C']
    wdata.weather_dict_now['humidity'] = json_body['response']['humidity']['percent']
    wdata.weather_dict_now['pressure'] = json_body['response']['pressure']['mm_hg_atm']
    wdata.weather_dict_now['wind_direction'] = json_body['response']['wind']['direction']['scale_8']
    wdata.weather_dict_now['wind_speed'] = json_body['response']['wind']['speed']['m_s']

    weather_result = f'\U0001F30E Город: {city}\n' \
                     f'\U0001F5D3 Дата: {wdata.weather_dict_now["date"]}\n' \
                     f'\U0001F4CB {wdata.weather_dict_now["description"]}\n' \
                     f'\U0001F321 Температура воздуха: {wdata.weather_dict_now["air_temperature"]}°C\n' \
                     f'\U0001F30A Температура воды: {wdata.weather_dict_now["water_temperature"]}°C\n' \
                     f'\U0001F4A7 Влажность: {wdata.weather_dict_now["humidity"]}%\n' \
                     f'\U0001F5FB Давление: {wdata.weather_dict_now["pressure"]} мм рт. ст.\n' \
                     f'\U0001F32A Ветер: {wdata.wind_dict[wdata.weather_dict_now["wind_direction"]]} {wdata.weather_dict_now["wind_speed"]} м/с\n\n' \
                     f'Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите дальнейшее действие"))


@router.message(States.getting_period, F.text.lower() == "сегодня")
async def getting_1d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']
    city: str = user_data['city_name']
    user_id: float = message.from_user.id

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url4}{city_id}/?days=1") as response:
                json_body = await response.json()
        wdata.weather_dict_1d['date'] = format_data(json_body['response'][1]['date']['local'][:10])
        logging.info(f'[+] Пользователь с id: {user_id} запросил период успешно')
    except Exception as ex:
        await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
        await state.set_state(States.getting_weather)
        logging.warning(f'[!!!] При запросе периода пользователем id: {user_id} произошла ошибка {ex}')

    for i in range(1, 9):
        wdata.weather_dict_1d[i]['time'] = json_body['response'][i - 1]['date']['local'][11:16]
        wdata.weather_dict_1d[i]['temperature'] = json_body['response'][i - 1]['temperature']['air']['C']
        wdata.weather_dict_1d[i]['wind_speed'] = json_body['response'][i - 1]['wind']['speed']['m_s']
        wdata.weather_dict_1d[i]['wind_direction'] = json_body['response'][i - 1]['wind']['direction']['scale_8']
        wdata.weather_dict_1d[i]['precipitation_amount'] = json_body['response'][i - 1]['precipitation']['amount']
        wdata.weather_dict_1d[i]['pressure'] = json_body['response'][i - 1]['pressure']['mm_hg_atm']

    weather_result = f'\U0001F30E Город: {city}\n\U0001F5D3 Дата: {wdata.weather_dict_1d["date"]}\n'

    for i in range(1, 9):
        weather_result += f'{smdata.smiles[i]} {wdata.weather_dict_1d[i]["time"]}:\n\U0001F321 {wdata.weather_dict_1d[i]["temperature"]}°C ' \
                          f'\U0001F5FB {wdata.weather_dict_1d[i]["pressure"]} мм рт. ст.\n' \
                          f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_1d[i]["wind_direction"]]} {wdata.weather_dict_1d[i]["wind_speed"]} м/с ' \
                          f'\U0001F327{wdata.weather_dict_1d[i]["precipitation_amount"]} мм\n'

    weather_result += f'\nИнформация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите дальнейшее действие"))


@router.message(States.getting_period, F.text.lower() == "завтра")
async def getting_1d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']
    user_id: float = message.from_user.id
    city: str = user_data['city_name']

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url4}{city_id}/?days=2") as response:
                json_body = await response.json()
        wdata.weather_dict_1d['date'] = format_data(json_body['response'][8]['date']['local'][:10])
        logging.info(f'[+] Пользователь с id: {user_id} запросил период успешно')
    except Exception as ex:
        await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
        await state.set_state(States.getting_weather)
        logging.warning(f'[!!!] При запросе периода пользователем id: {user_id} произошла ошибка {ex}')

    for i in range(1, 9):
        wdata.weather_dict_1d[i]['time'] = json_body['response'][i + 7]['date']['local'][11:16]
        wdata.weather_dict_1d[i]['temperature'] = json_body['response'][i + 7]['temperature']['air']['C']
        wdata.weather_dict_1d[i]['wind_speed'] = json_body['response'][i + 7]['wind']['speed']['m_s']
        wdata.weather_dict_1d[i]['wind_direction'] = json_body['response'][i + 7]['wind']['direction']['scale_8']
        wdata.weather_dict_1d[i]['precipitation_amount'] = json_body['response'][i + 7]['precipitation']['amount']
        wdata.weather_dict_1d[i]['pressure'] = json_body['response'][i + 7]['pressure']['mm_hg_atm']

    weather_result = f'\U0001F30E Город: {city}\n\U0001F5D3 Дата: {wdata.weather_dict_1d["date"]}\n'

    for i in range(1, 9):
        weather_result += f'{smdata.smiles[i]} {wdata.weather_dict_1d[i]["time"]}:\n\U0001F321 {wdata.weather_dict_1d[i]["temperature"]}°C ' \
                          f'\U0001F5FB {wdata.weather_dict_1d[i]["pressure"]} мм рт. ст.\n' \
                          f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_1d[i]["wind_direction"]]} {wdata.weather_dict_1d[i]["wind_speed"]} м/с ' \
                          f'\U0001F327{wdata.weather_dict_1d[i]["precipitation_amount"]} мм\n'

    weather_result += f'\nИнформация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите дальнейшее действие"))


@router.message(States.getting_period, F.text.lower() == "3 дня")
async def getting_3d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']
    city: str = user_data['city_name']
    user_id: float = message.from_user.id

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url3}{city_id}/?&days=3") as response:
                json_body = await response.json()

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

    except Exception as ex:
        await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
        await state.set_state(States.getting_weather)
        logging.warning(f'[!!!] При запросе периода пользователем id: {user_id} произошла ошибка {ex}')

    weather_result = f'\U0001F30E Город: {city}\n'

    date_i = 0
    for i in range(1, 4):
        weather_result += "\U0001F5D3 Дата: " + format_data(json_body['response'][date_i]['date']['local'][:10]) + "\n\n"
        date_i += 4
        for j in range(1, 5):
            if j == 1:
                weather_result += f'\U0001F311 Ночь: '
            elif j == 2:
                weather_result += f'\U0001F316 Утро: '
            elif j == 3:
                weather_result += f'\U00002600 День: '
            else:
                weather_result += f'\U0001F312 Вечер: '
            weather_result += f'\U0001F321 {wdata.weather_dict_3d[i][j]["temperature"]}°C ' \
                              f'\U0001F327 {wdata.weather_dict_3d[i][j]["precipitation_amount"]} мм ' \
                              f'\U0001F4A7{wdata.weather_dict_3d[i][j]["humidity"]}%\n'
            if j == 4:
                weather_result += f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[i][j]["wind_direction"]]} {wdata.weather_dict_3d[i][j]["wind_speed"]} м/с\n\n'
            else:
                weather_result += f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_3d[i][j]["wind_direction"]]} {wdata.weather_dict_3d[i][j]["wind_speed"]} м/с\n'

    weather_result += f'Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите дальнейшее действие"))


@router.message(States.getting_period, F.text.lower() == "7 дней")
async def getting_1d_weather(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city_id: int = user_data['city_id']
    city: str = user_data['city_name']
    user_id: float = message.from_user.id

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{url5}{city_id}/?days=7") as response:
                json_body = await response.json()

        for i in range(1, 8):
            wdata.weather_dict_7d[i]['date'] = format_data(json_body['response'][i - 1]['date']['local'])
            wdata.weather_dict_7d[i]['temperature_max'] = json_body['response'][i - 1]['temperature']['air']['max']['C']
            wdata.weather_dict_7d[i]['temperature_min'] = json_body['response'][i - 1]['temperature']['air']['min']['C']
            wdata.weather_dict_7d[i]['wind_speed_avg'] = json_body['response'][i - 1]['wind']['speed']['max']['m_s']
            wdata.weather_dict_7d[i]['wind_direction'] = json_body['response'][i - 1]['wind']['direction']['max']['scale_8']
            wdata.weather_dict_7d[i]['precipitation_amount'] = json_body['response'][i - 1]['precipitation']['amount']
            wdata.weather_dict_7d[i]['pressure_max'] = json_body['response'][i - 1]['pressure']['mm_hg_atm']['max']
            wdata.weather_dict_7d[i]['pressure_min'] = json_body['response'][i - 1]['pressure']['mm_hg_atm']['min']

    except Exception as ex:
        await message.answer("Произошла ошибка сервера, попробуйте позже.", reply_markup=get_weather_keyboard())
        await state.set_state(States.getting_weather)
        logging.warning(f'[!!!] При запросе периода пользователем id: {user_id} произошла ошибка {ex}')

    weather_result = f'\U0001F30E Город: {city}\n'

    for i in range(1, 8):
        weather_result += f'\U0001F5D3 Дата: {wdata.weather_dict_7d[i]["date"]}\n\n' \
                          f'\U0001F321 {wdata.weather_dict_7d[i]["temperature_min"]} - {wdata.weather_dict_7d[i]["temperature_max"]}°C ' \
                          f'\U0001F327 {wdata.weather_dict_7d[i]["precipitation_amount"]} мм\n' \
                          f'\U0001F32A {wdata.wind_dict[wdata.weather_dict_7d[i]["wind_direction"]]} {wdata.weather_dict_7d[i]["wind_speed_avg"]} м/с\n' \
                          f'\U0001F5FB {wdata.weather_dict_7d[i]["pressure_min"]} - {wdata.weather_dict_7d[i]["pressure_max"]} мм рт. ст.\n\n'

    weather_result += f'Информация о погоде взята с сайта <a href="gismeteo.ru">Gismeteo</a>'

    await state.set_state(States.next_choice)
    await message.answer(weather_result, parse_mode="HTML")
    await message.answer("Выберите дальнейшее действие", reply_markup=get_next_choice_keyboard().as_markup(resize_keyboard=True, input_field_placeholder="Выберите дальнейшее действие"))


@router.message(States.getting_period)
async def wrong_choice(message: Message):
    await message.answer("Так не пойдет, нажмите на кнопку!")

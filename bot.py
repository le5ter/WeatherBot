import asyncio
import logging
import datetime
import redis
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv, find_dotenv
from handlers import common, weather

load_dotenv(find_dotenv())

tz = datetime.timezone(datetime.timedelta(hours=3), name='МСК')
format_time = f'{datetime.datetime.now(tz=tz):%Y-%m-%d %H:%M:%S}'

r = redis.Redis(password=f'{os.getenv("REDIS_PAS")}')


async def main():
    logging.basicConfig(level=logging.INFO, filename='bot.log',
                        format=f'{format_time} - %(name)s - %(levelname)s - %(message)s')
    bot = Bot(token=f'{os.getenv("BOT_TOKEN")}')
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(weather.router)
    logging.info("[!] Бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

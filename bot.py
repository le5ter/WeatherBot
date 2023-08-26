import asyncio
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv, find_dotenv
from handlers import common, weather

load_dotenv(find_dotenv())


async def main():
    bot = Bot(token=f'{os.getenv("BOT_TOKEN")}')
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(weather.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

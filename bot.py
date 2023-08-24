from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


bot = Bot(token=f'{os.getenv("BOT_TOKEN")}')
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Здесь что-то будет")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    main()
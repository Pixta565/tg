import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from db.database import init_db
from bot.handlers import user, resume, vacancy, response

load_dotenv(dotenv_path="D:/Учеба/ГУАП/6 семестр/Python/Praktik #7/job_search_bot/.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    init_db()  # создание таблиц и категорий

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user.router)
    dp.include_router(resume.router)
    dp.include_router(vacancy.router)
    dp.include_router(response.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
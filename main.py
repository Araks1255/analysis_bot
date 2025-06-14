import asyncio

from aiogram import Bot, Dispatcher

from config import TOKEN

from app import handlers, spending_analysis


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(
       handlers.router,
       spending_analysis.router
    )
    await dp.start_polling(bot)
    
if __name__ == '__main__':
    asyncio.run(main())
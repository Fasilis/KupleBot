import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


from handlers import pay, me, refund, gifts, callbacks

def setup_routers(dp: Dispatcher):
    dp.include_router(pay.router)
    dp.include_router(me.router)
    dp.include_router(refund.router)
    dp.include_router(gifts.router)
    dp.include_router(callbacks.router)

async def main():
    setup_routers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

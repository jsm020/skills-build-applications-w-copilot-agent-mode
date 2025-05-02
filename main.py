import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import channel, user
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_routers(channel.router, user.router)

    # Notify all admins that the bot has started
    from config import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "✅ Auction bot started and is online.")
        except Exception:
            pass

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

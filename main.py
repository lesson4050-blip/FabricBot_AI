import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import settings
from handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("FabricBot_AI")

async def main():
    logger.info("Initializing FabricBot AI (Claude + 1C ERP)...")
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    dp.include_router(router)
    
    logger.info("Bot configured. Ready for polling/webhooks.")
    if settings.telegram_bot_token == "mock_bot_token":
        logger.info("Running in offline validation mode. Mock services active.")
        return

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("FabricBot AI stopped.")

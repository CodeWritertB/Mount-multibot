import asyncio
import logging
from aiogram import Bot, Dispatcher
from vkbottle.bot import Bot as VKBot
from aiohttp import web
from src.config import config
from src.telegram.handlers import router as telegram_router
from src.admin.handlers import router as admin_router
from src.adapters.telegram import TelegramAdapter
from src.adapters.vk import VKAdapter, vk_bot
from src.adapters.max import MaxAdapter
from src.core.broadcast import platform_senders
from src.core.webhooks import create_webhook_app
from src.core.birthday import check_and_send_birthdays
from src.database.session import AsyncSessionLocal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def start_telegram():
    """
    Запуск Telegram бота
    
    Создает бота, диспетчер и запускает polling
    """
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    
    # Создаем адаптер и регистрируем его в platform_senders
    tg_adapter = TelegramAdapter(bot)
    platform_senders["telegram"] = tg_adapter.send_message
    
    # Подключаем роутеры
    dp.include_router(telegram_router)
    dp.include_router(admin_router)
    
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


async def start_vk():
    """
    Запуск VK бота
    
    Создает адаптер и запускает polling
    """
    vk_adapter = VKAdapter(vk_bot)
    platform_senders["vk"] = vk_adapter.send_message
    
    logger.info("Starting VK bot...")
    await vk_bot.run_polling()


async def start_max():
    """
    Запуск Max бота
    
    Создает адаптер и запускает обработку событий
    """
    max_adapter = MaxAdapter()
    platform_senders["max"] = max_adapter.send_message
    
    logger.info("Starting Max bot...")
    # В реальном приложении здесь будет запуск обработки событий Max API
    # Для простоты просто зацикливаем
    while True:
        await asyncio.sleep(3600)


async def start_webhook_server():
    """
    Запуск сервера для обработки webhook от ЮKassa
    
    Обрабатывает уведомления о платежах
    """
    app = create_webhook_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    logger.info("Starting Webhook server on port 8080...")
    await site.start()
    
    # Бесконечный цикл для поддержания работы сервера
    while True:
        await asyncio.sleep(3600)


async def run_birthday_scheduler():
    """
    Планировщик поздравлений с днём рождения
    
    Запускается как отдельная задача
    Проверяет дни рождения каждые 24 часа
    """
    logger.info("Starting Birthday scheduler...")
    
    while True:
        async with AsyncSessionLocal() as session:
            try:
                await check_and_send_birthdays(session)
            except Exception as e:
                logger.error(f"Error in birthday scheduler: {e}")
        
        # Запуск каждые 24 часа (86400 секунд)
        await asyncio.sleep(86400)


async def main():
    """
    Главная функция запуска всех компонентов
    
    Запускает Telegram, VK, Max ботов и webhook сервер параллельно
    """
    # Запускаем только Telegram бота для тестирования
    # Остальные платформы требуют отдельных event loop
    await start_telegram()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

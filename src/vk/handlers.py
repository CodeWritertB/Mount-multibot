from vkbottle.bot import Bot, Message
from src.adapters import BaseAdapter
from src.core.booking import get_user_by_platform, create_user
from src.database.session import AsyncSessionLocal
from src.config import config

# Создаем глобальный экземпляр бота VK
vk_bot = Bot(token=config.VK_API_SECRET.get_secret_value())


@vk_bot.on.message(text=["Начать", "start", "/start"])
async def start_handler(message: Message):
    """
    Обработчик команды /start для VK
    Проверяет, зарегистрирован ли пользователь
    """
    async with AsyncSessionLocal() as session:
        user = await get_user_by_platform(session, "vk", message.from_id)
        if not user:
            await message.answer(
                "Добро пожаловать в «Маунт»! Пожалуйста, пройдите регистрацию в Telegram боте "
                "для полного доступа или напишите ваше ФИО здесь."
            )
        else:
            await message.answer(
                f"С возвращением, {user.full_name}! "
                "Для бронирования используйте наше приложение или Telegram бот."
            )


@vk_bot.on.message(text="Профиль")
async def profile_handler(message: Message):
    """
    Обработчик команды "Профиль" для VK
    Показывает данные пользователя
    """
    async with AsyncSessionLocal() as session:
        user = await get_user_by_platform(session, "vk", message.from_id)
        if user:
            await message.answer(
                f"Ваш профиль: {user.full_name}, Телефон: {user.phone}"
            )
        else:
            await message.answer("Вы не зарегистрированы.")


@vk_bot.on.message(text=["Бронь", "Забронировать", "/book"])
async def book_handler(message: Message):
    """
    Обработчик команды бронирования для VK
    Перенаправляет в Telegram для полного процесса
    """
    await message.answer(
        "Для бронирования стола перейдите в Telegram бот: @your_bot_name"
    )

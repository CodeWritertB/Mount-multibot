from aiogram import Bot
from src.adapters import BaseAdapter
from typing import Optional


class TelegramAdapter(BaseAdapter):
    """
    Адаптер для Telegram бота
    Реализует отправку сообщений через aiogram
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализация адаптера
        :param bot: Экземпляр Bot из aiogram
        """
        self.bot = bot

    async def send_message(self, user_id: int, text: str, image_url: Optional[str] = None):
        """
        Отправка сообщения пользователю
        Если есть image_url - отправляет фото с подписью
        Иначе отправляет текстовое сообщение
        """
        if image_url:
            await self.bot.send_photo(
                chat_id=user_id, 
                photo=image_url, 
                caption=text
            )
        else:
            await self.bot.send_message(chat_id=user_id, text=text)

    async def send_notification(self, user_id: int, text: str):
        """
        Отправка уведомления пользователю
        Добавляет иконку уведомления к тексту
        """
        await self.bot.send_message(chat_id=user_id, text=f"🔔 {text}")

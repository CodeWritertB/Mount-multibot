from vkbottle.bot import Bot
from src.adapters import BaseAdapter
from typing import Optional
from src.config import config

# Создаем глобальный экземпляр бота VK
vk_bot = Bot(token=config.VK_API_SECRET.get_secret_value())


class VKAdapter(BaseAdapter):
    """
    Адаптер для VK бота
    Реализует отправку сообщений через vkbottle
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализация адаптера
        :param bot: Экземпляр Bot из vkbottle
        """
        self.bot = bot

    async def send_message(self, user_id: int, text: str, image_url: Optional[str] = None):
        """
        Отправка сообщения пользователю
        Если есть image_url - добавляет ссылку в текст
        Иначе отправляет текстовое сообщение
        """
        if image_url:
            # В реальном приложении используем PhotoMessageUploader
            await self.bot.api.messages.send(
                user_id=user_id, 
                message=f"{text}\n{image_url}", 
                random_id=0
            )
        else:
            await self.bot.api.messages.send(
                user_id=user_id, 
                message=text, 
                random_id=0
            )

    async def send_notification(self, user_id: int, text: str):
        """
        Отправка уведомления пользователю
        Добавляет иконку уведомления к тексту
        """
        await self.bot.api.messages.send(
            user_id=user_id, 
            message=f"🔔 {text}", 
            random_id=0
        )

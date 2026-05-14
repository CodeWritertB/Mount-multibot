from typing import Optional, Protocol
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(Protocol):
    """
    Базовый класс для адаптеров платформ
    Определяет интерфейс для отправки сообщений
    """
    
    async def send_message(self, user_id: int, text: str, image_url: Optional[str] = None) -> None:
        """
        Отправка сообщения пользователю
        :param user_id: ID пользователя
        :param text: Текст сообщения
        :param image_url: URL картинки (опционально)
        """
        ...

    async def send_notification(self, user_id: int, text: str) -> None:
        """
        Отправка уведомления пользователю
        :param user_id: ID пользователя
        :param text: Текст уведомления
        """
        ...


class MaxAdapter(BaseAdapter):
    """
    Адаптер для Max API
    Реализует отправку сообщений через Max API
    """
    
    def __init__(self, api_client=None):
        """
        Инициализация адаптера
        :param api_client: Клиент для работы с Max API (опционально)
        """
        self.api_client = api_client

    async def send_message(self, user_id: int, text: str, image_url: Optional[str] = None):
        """
        Отправка сообщения пользователю через Max API
        """
        logger.info(f"Sending Max message to {user_id}: {text}")
        # Implementation for Max API would go here
        # Пример:
        # if self.api_client:
        #     await self.api_client.send_message(user_id, text, image_url)
        pass

    async def send_notification(self, user_id: int, text: str):
        """
        Отправка уведомления пользователю через Max API
        """
        logger.info(f"Sending Max notification to {user_id}: {text}")
        # Implementation for Max API would go here
        pass

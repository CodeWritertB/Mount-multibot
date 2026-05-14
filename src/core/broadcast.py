import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User

# Словарь для хранения функций отправки сообщений для каждой платформы
# Инициализируется в main.py при запуске
platform_senders = {
    "telegram": None,
    "vk": None,
    "max": None
}


async def send_broadcast(
    session: AsyncSession,
    text: str,
    image_url: Optional[str] = None,
    platform: Optional[str] = None
):
    """
    Отправка рассылки пользователям
    
    :param session: Сессия БД
    :param text: Текст сообщения
    :param image_url: URL картинки (опционально)
    :param platform: Платформа для рассылки (опционально)
    """
    # Получаем всех незабаненных пользователей
    stmt = select(User).where(User.is_banned == False)
    
    # Если указана платформа, фильтруем по ней
    if platform:
        if platform == "telegram":
            stmt = stmt.where(User.telegram_id.isnot(None))
        elif platform == "vk":
            stmt = stmt.where(User.vk_id.isnot(None))
        elif platform == "max":
            stmt = stmt.where(User.max_id.isnot(None))
            
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    # Отправляем сообщение каждому пользователю
    for user in users:
        # Telegram
        if user.telegram_id and platform_senders["telegram"] and (not platform or platform == "telegram"):
            await platform_senders["telegram"](user.telegram_id, text, image_url)
        # VK
        elif user.vk_id and platform_senders["vk"] and (not platform or platform == "vk"):
            await platform_senders["vk"](user.vk_id, text, image_url)
        # Max
        elif user.max_id and platform_senders["max"] and (not platform or platform == "max"):
            await platform_senders["max"](user.max_id, text, image_url)


async def send_birthday_message(
    session: AsyncSession,
    user_id: uuid.UUID,
    message_text: str,
    platform: str
):
    """
    Отправка поздравления с днём рождения
    
    :param session: Сессия БД
    :param user_id: ID пользователя
    :param message_text: Текст поздравления
    :param platform: Платформа (telegram, vk, max)
    """
    from src.database.models import BirthdayMessage
    from datetime import datetime
    
    # Отправляем сообщение
    if platform == "telegram" and platform_senders["telegram"]:
        await platform_senders["telegram"](user_id, message_text)
    elif platform == "vk" and platform_senders["vk"]:
        await platform_senders["vk"](user_id, message_text)
    elif platform == "max" and platform_senders["max"]:
        await platform_senders["max"](user_id, message_text)
    
    # Записываем в историю
    log = BirthdayMessage(
        user_id=user_id,
        message_text=message_text,
        sent_at=datetime.now(),
        status="sent",
        platform=platform
    )
    session.add(log)
    await session.commit()

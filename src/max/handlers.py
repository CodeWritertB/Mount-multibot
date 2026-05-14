from src.adapters.max import MaxAdapter
from src.core.booking import get_user_by_platform, create_user
from src.database.session import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)


async def handle_max_event(event):
    """
    Обработчик событий от Max API
    Обрабатывает входящие сообщения и вызовы
    """
    event_type = event.get("type")
    
    if event_type == "message_new":
        message = event["object"]["message"]
        user_id = message.get("from_id")
        text = message.get("text", "").strip()
        
        async with AsyncSessionLocal() as session:
            user = await get_user_by_platform(session, "max", user_id)
            
            if text.lower() in ["начать", "start", "/start"]:
                if not user:
                    await send_message(user_id, "Добро пожаловать в «Маунт»! Пожалуйста, пройдите регистрацию.")
                else:
                    await send_message(user_id, f"С возвращением, {user.full_name}!")
            
            elif text.lower() == "профиль":
                if user:
                    await send_message(user_id, f"Ваш профиль: {user.full_name}, Телефон: {user.phone}")
                else:
                    await send_message(user_id, "Вы не зарегистрированы.")
            
            elif text.lower() in ["бронь", "забронировать", "/book"]:
                await send_message(user_id, "Для бронирования стола используйте Telegram бот.")
            
            else:
                await send_message(user_id, "Я не понимаю эту команду. Попробуйте /start")


async def send_message(user_id: int, text: str):
    """
    Отправка сообщения через Max API
    """
    logger.info(f"Sending Max message to {user_id}: {text}")
    # Implementation for Max API would go here
    pass

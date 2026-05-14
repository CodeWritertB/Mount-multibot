from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from src.database.session import AsyncSessionLocal
from src.core.booking import get_user_by_platform


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для передачи сессии БД в обработчики
    Создает асинхронную сессию и передает её в handler через data
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)


class CheckBanMiddleware(BaseMiddleware):
    """
    Middleware для проверки, не забанен ли пользователь
    Прерывает выполнение, если пользователь заблокирован
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        session = data.get("session")
        if not session:
            # Если сессии нет, пропускаем проверку
            return await handler(event, data)
        
        user = await get_user_by_platform(session, "telegram", event.from_user.id)
        if user and user.is_banned:
            await event.answer("Вы заблокированы в системе.")
            return
        return await handler(event, data)

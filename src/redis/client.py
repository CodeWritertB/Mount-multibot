import redis.asyncio as redis
from src.config import config

# Создание клиента Redis
redis_client = redis.from_url(str(config.REDIS_URL), decode_responses=True)


async def block_slot(table_id: str, booking_date: str, start_time: str, ttl: int = 600) -> bool:
    """
    Блокировка слота времени в Redis
    
    Используется для предотвращения double booking
    Слот блокируется на 10 минут (600 секунд по умолчанию)
    
    :param table_id: ID стола
    :param booking_date: Дата бронирования (YYYY-MM-DD)
    :param start_time: Время начала (HH:MM)
    :param ttl: Время жизни блокировки в секундах
    :return: True если блокировка успешна, False если уже заблокировано
    """
    key = f"block:{table_id}:{booking_date}:{start_time}"
    # Используем nx=True для атомарной операции set-if-not-exists
    return await redis_client.set(key, "blocked", ex=ttl, nx=True)


async def is_slot_blocked(table_id: str, booking_date: str, start_time: str) -> bool:
    """
    Проверка, заблокирован ли слот времени
    
    :param table_id: ID стола
    :param booking_date: Дата бронирования (YYYY-MM-DD)
    :param start_time: Время начала (HH:MM)
    :return: True если заблокировано
    """
    key = f"block:{table_id}:{booking_date}:{start_time}"
    return await redis_client.exists(key)


async def release_slot(table_id: str, booking_date: str, start_time: str) -> bool:
    """
    Освобождение заблокированного слота времени
    
    :param table_id: ID стола
    :param booking_date: Дата бронирования (YYYY-MM-DD)
    :param start_time: Время начала (HH:MM)
    :return: True если слот был заблокирован и освобожден
    """
    key = f"block:{table_id}:{booking_date}:{start_time}"
    return await redis_client.delete(key)


async def get_blocked_slots(table_id: str, booking_date: str) -> list:
    """
    Получение всех заблокированных слотов для стола на дату
    
    :param table_id: ID стола
    :param booking_date: Дата бронирования (YYYY-MM-DD)
    :return: Список заблокированных временных слотов
    """
    pattern = f"block:{table_id}:{booking_date}:*"
    keys = await redis_client.keys(pattern)
    slots = [key.split(":")[-1] for key in keys]
    return slots

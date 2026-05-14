import uuid
from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Booking, Table, User
from src.redis.client import block_slot, is_slot_blocked, release_slot


async def get_available_tables(
    session: AsyncSession,
    booking_date: date,
    start_time: time,
    end_time: time,
    guests_count: int
) -> List[Table]:
    """
    Получение списка доступных столов на заданное время
    
    :param session: Сессия БД
    :param booking_date: Дата бронирования
    :param start_time: Время начала
    :param end_time: Время окончания
    :param guests_count: Количество гостей
    :return: Список доступных столов
    """
    # Сначала получаем все столы, подходящие по вместимости
    stmt = select(Table).where(
        and_(
            Table.is_active == True,
            Table.capacity >= guests_count
        )
    )
    result = await session.execute(stmt)
    tables = result.scalars().all()
    
    available_tables = []
    for table in tables:
        # Проверяем, заблокирован ли стол в Redis
        if await is_slot_blocked(str(table.id), str(booking_date), str(start_time)):
            continue
            
        # Проверяем, нет ли конфликтующих броней
        booking_stmt = select(Booking).where(
            and_(
                Booking.table_id == table.id,
                Booking.booking_date == booking_date,
                Booking.status.in_(["confirmed", "paid", "pending"]),
                or_(
                    # Бронь перекрывает начало нашей брони
                    and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                    # Бронь перекрывает конец нашей брони
                    and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                    # Наша бронь полностью внутри другой брони
                    and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
                )
            )
        )
        booking_result = await session.execute(booking_stmt)
        if not booking_result.scalars().first():
            available_tables.append(table)
            
    return available_tables


async def create_booking(
    session: AsyncSession,
    user_id: uuid.UUID,
    table_id: uuid.UUID,
    booking_date: date,
    start_time: time,
    end_time: time,
    guests_count: int,
    deposit_amount: float
) -> Booking:
    """
    Создание брони стола
    
    :param session: Сессия БД
    :param user_id: ID пользователя
    :param table_id: ID стола
    :param booking_date: Дата бронирования
    :param start_time: Время начала
    :param end_time: Время окончания
    :param guests_count: Количество гостей
    :param deposit_amount: Сумма депозита
    :return: Созданная бронь
    :raises Exception: Если стол уже забронирован
    """
    # Блокируем слот в Redis на 10 минут (600 секунд)
    if not await block_slot(str(table_id), str(booking_date), str(start_time)):
        raise Exception("Стол уже забронирован или временно заблокирован")
        
    try:
        booking = Booking(
            user_id=user_id,
            table_id=table_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            guests_count=guests_count,
            deposit_amount=deposit_amount,
            status="pending"
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking
    except Exception as e:
        # Если ошибка при создании брони, освобождаем слот в Redis
        await release_slot(str(table_id), str(booking_date), str(start_time))
        raise e


async def get_user_by_platform(
    session: AsyncSession,
    platform: str,
    platform_id: int
) -> Optional[User]:
    """
    Получение пользователя по ID платформы
    
    :param session: Сессия БД
    :param platform: Название платформы (telegram, vk, max)
    :param platform_id: ID пользователя в платформе
    :return: Пользователь или None
    """
    if platform == "telegram":
        stmt = select(User).where(User.telegram_id == platform_id)
    elif platform == "vk":
        stmt = select(User).where(User.vk_id == platform_id)
    elif platform == "max":
        stmt = select(User).where(User.max_id == platform_id)
    else:
        return None
        
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_user(
    session: AsyncSession,
    full_name: str,
    phone: str,
    platform: str,
    platform_id: int,
    birth_date: Optional[date] = None
) -> User:
    """
    Создание нового пользователя
    
    :param session: Сессия БД
    :param full_name: ФИО пользователя
    :param phone: Номер телефона
    :param platform: Платформа (telegram, vk, max)
    :param platform_id: ID пользователя в платформе
    :param birth_date: Дата рождения (опционально)
    :return: Созданный пользователь
    """
    user_data = {
        "full_name": full_name,
        "phone": phone
    }
    
    if platform == "telegram":
        user_data["telegram_id"] = platform_id
    elif platform == "vk":
        user_data["vk_id"] = platform_id
    elif platform == "max":
        user_data["max_id"] = platform_id
        
    if birth_date:
        user_data["birth_date"] = birth_date
        
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_table_price(session: AsyncSession, table_id: uuid.UUID) -> float:
    """
    Получение цены стола за час
    
    :param session: Сессия БД
    :param table_id: ID стола
    :return: Цена за час
    """
    stmt = select(Table.price_per_hour).where(Table.id == table_id)
    result = await session.execute(stmt)
    price = result.scalar()
    return float(price) if price else 0.0


async def calculate_booking_price(
    session: AsyncSession,
    table_id: uuid.UUID,
    start_time: time,
    end_time: time
) -> float:
    """
    Расчет стоимости брони
    
    :param session: Сессия БД
    :param table_id: ID стола
    :param start_time: Время начала
    :param end_time: Время окончания
    :return: Стоимость брони
    """
    price_per_hour = await get_table_price(session, table_id)
    
    # Расчет длительности в часах
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    duration_minutes = end_minutes - start_minutes
    duration_hours = duration_minutes / 60
    
    return price_per_hour * duration_hours

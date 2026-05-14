import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Promocode, Booking, BookingPromocode


async def validate_promo(
    session: AsyncSession,
    code: str,
    platform: str
) -> Optional[Promocode]:
    """
    Валидация промокода
    
    :param session: Сессия БД
    :param code: Код промокода
    :param platform: Платформа (telegram, vk, max)
    :return: Промокод если валиден, иначе None
    """
    stmt = select(Promocode).where(
        and_(
            Promocode.code == code,
            Promocode.is_active == True,
            Promocode.valid_from <= datetime.now(),
            Promocode.valid_to >= datetime.now()
        )
    )
    result = await session.execute(stmt)
    promo = result.scalars().first()
    
    if not promo:
        return None
        
    # Проверка лимита использований
    if promo.max_uses > 0 and promo.current_uses >= promo.max_uses:
        return None
        
    # Проверка ограничения по платформе
    if promo.platform and promo.platform != platform:
        return None
        
    return promo


async def apply_promo_to_booking(
    session: AsyncSession,
    booking_id: uuid.UUID,
    promo_id: uuid.UUID
) -> Decimal:
    """
    Применение промокода к бронированию
    
    :param session: Сессия БД
    :param booking_id: ID бронирования
    :param promo_id: ID промокода
    :return: Размер скидки
    :raises Exception: Если бронь или промокод не найдены
    """
    # Получаем бронь и промокод
    booking_stmt = select(Booking).where(Booking.id == booking_id)
    promo_stmt = select(Promocode).where(Promocode.id == promo_id)
    
    booking = (await session.execute(booking_stmt)).scalars().first()
    promo = (await session.execute(promo_stmt)).scalars().first()
    
    if not booking or not promo:
        raise Exception("Бронирование или промокод не найдены")
        
    # Расчет скидки
    discount_applied = Decimal("0.00")
    if promo.discount_type == "percentage":
        discount_applied = booking.deposit_amount * (promo.discount_value / Decimal("100"))
    elif promo.discount_type == "fixed":
        discount_applied = promo.discount_value
        
    # Скидка не может превышать сумму депозита
    discount_applied = min(discount_applied, booking.deposit_amount)
    
    # Обновляем сумму депозита
    booking.deposit_amount -= discount_applied
    
    # Увеличиваем счетчик использований
    promo.current_uses += 1
    
    # Записываем использование промокода
    booking_promo = BookingPromocode(
        booking_id=booking_id,
        promocode_id=promo_id,
        discount_applied=discount_applied
    )
    session.add(booking_promo)
    
    await session.commit()
    return discount_applied


async def get_user_promocodes(
    session: AsyncSession,
    user_id: uuid.UUID,
    platform: str
) -> list:
    """
    Получение активных промокодов пользователя
    
    :param session: Сессия БД
    :param user_id: ID пользователя
    :param platform: Платформа
    :return: Список промокодов
    """
    stmt = select(Promocode).where(
        and_(
            Promocode.is_active == True,
            Promocode.valid_from <= datetime.now(),
            Promocode.valid_to >= datetime.now(),
            or_(
                Promocode.platform == None,
                Promocode.platform == platform
            )
        )
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def increment_promo_uses(session: AsyncSession, promo_id: uuid.UUID):
    """
    Увеличение счетчика использований промокода
    
    :param session: Сессия БД
    :param promo_id: ID промокода
    """
    stmt = (
        update(Promocode)
        .where(Promocode.id == promo_id)
        .values(current_uses=Promocode.current_uses + 1)
    )
    await session.execute(stmt)
    await session.commit()

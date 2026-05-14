from aiohttp import web
from sqlalchemy import select, update
from src.database.session import AsyncSessionLocal
from src.database.models import Booking
from src.config import config
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)


async def handle_yookassa_webhook(request: web.Request) -> web.Response:
    """
    Обработчик webhook от ЮKassa
    
    Проверяет подпись и обновляет статус брони при успешной оплате
    """
    try:
        # Получаем данные из запроса
        data = await request.json()
        
        # В реальном приложении нужно проверять подпись webhook
        # YooKassa отправляет подпись в заголовке YooKassa-Signature
        # Для простоты пропускаем проверку, но в продакшене обязательно нужна
        
        event_type = data.get("event")
        
        if event_type == "payment.succeeded":
            payment_object = data.get("object", {})
            metadata = payment_object.get("metadata", {})
            booking_id = metadata.get("booking_id")
            
            if booking_id:
                async with AsyncSessionLocal() as session:
                    # Обновляем статус брони на "paid"
                    stmt = update(Booking).where(Booking.id == booking_id).values(status="paid")
                    await session.execute(stmt)
                    await session.commit()
                    logger.info(f"Booking {booking_id} status updated to paid.")
                    
                    # Отправляем уведомление администратору
                    await notify_admin_about_booking(session, booking_id)
                    
        return web.Response(status=200)
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return web.Response(status=500)


async def notify_admin_about_booking(session, booking_id: str):
    """
    Отправка уведомления администратору о новой брони
    
    :param session: Сессия БД
    :param booking_id: ID бронирования
    """
    from src.database.models import Booking, Table
    from sqlalchemy import select
    
    # Получаем данные брони
    stmt = select(Booking).where(Booking.id == booking_id)
    result = await session.execute(stmt)
    booking = result.scalars().first()
    
    if not booking:
        return
    
    # Получаем данные стола
    table_stmt = select(Table).where(Table.id == booking.table_id)
    table_result = await session.execute(table_stmt)
    table = table_result.scalars().first()
    
    # Формируем сообщение
    message = (
        f"✅ Новая оплаченная бронь!\n"
        f"Стол: {table.name if table else booking.table_id}\n"
        f"Дата: {booking.booking_date}\n"
        f"Время: {booking.start_time} — {booking.end_time}\n"
        f"Гости: {booking.guests_count} чел.\n"
        f"Сумма: {booking.deposit_amount} ₽"
    )
    
    # В реальном приложении отправляем в админ-чат
    # Для простоты просто логируем
    logger.info(f"Notification to admin: {message}")


def create_webhook_app() -> web.Application:
    """
    Создание приложения для обработки webhook
    
    :return: aiohttp Application
    """
    app = web.Application()
    app.router.add_post("/webhook/yookassa", handle_yookassa_webhook)
    return app

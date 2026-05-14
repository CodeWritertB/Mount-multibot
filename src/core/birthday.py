from datetime import date, datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, BirthdayMessage
from src.core.broadcast import platform_senders


async def check_and_send_birthdays(session: AsyncSession):
    """
    Ежедневная проверка дат рождения и отправка поздравлений
    Запускается через scheduler в main.py
    """
    today = date.today()
    
    # Выбираем пользователей, у которых сегодня день рождения
    # Игнорируем год, сравниваем только месяц и день
    stmt = select(User).where(
        and_(
            func.extract('month', User.birth_date) == today.month,
            func.extract('day', User.birth_date) == today.day,
            User.is_banned == False
        )
    )
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    for user in users:
        # Проверяем, не отправляли ли уже поздравление сегодня
        sent_stmt = select(BirthdayMessage).where(
            and_(
                BirthdayMessage.user_id == user.id,
                func.cast(BirthdayMessage.created_at, func.Date) == today
            )
        )
        sent_result = await session.execute(sent_stmt)
        if sent_result.scalars().first():
            continue
            
        # Генерируем персонализированное поздравление
        message_text = (
            f"🎉 С днём рождения, {user.full_name}!\n\n"
            f"Спасибо, что выбираете «Маунт»! Дарим вам промокод BIRTHDAY15 на скидку 15%."
        )
        
        status = "sent"
        platform = None
        
        try:
            # Отправляем через соответствующую платформу
            if user.telegram_id and platform_senders["telegram"]:
                await platform_senders["telegram"](user.telegram_id, message_text)
                platform = "telegram"
            elif user.vk_id and platform_senders["vk"]:
                await platform_senders["vk"](user.vk_id, message_text)
                platform = "vk"
            elif user.max_id and platform_senders["max"]:
                await platform_senders["max"](user.max_id, message_text)
                platform = "max"
            else:
                status = "failed"
        except Exception as e:
            status = "failed"
            print(f"Ошибка отправки поздравления: {e}")
            
        # Записываем в историю
        log = BirthdayMessage(
            user_id=user.id,
            message_text=message_text,
            sent_at=datetime.now() if status == "sent" else None,
            status=status,
            platform=platform
        )
        session.add(log)
        
    await session.commit()


async def send_manual_birthday_message(
    session: AsyncSession,
    user_id: uuid.UUID
) -> bool:
    """
    Ручная отправка поздравления с днём рождения
    
    :param session: Сессия БД
    :param user_id: ID пользователя
    :return: True если отправлено успешно
    """
    from src.database.models import User
    import uuid
    
    # Получаем пользователя
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        return False
        
    # Проверяем, не отправляли ли уже сегодня
    today = date.today()
    sent_stmt = select(BirthdayMessage).where(
        and_(
            BirthdayMessage.user_id == user_id,
            func.cast(BirthdayMessage.created_at, func.Date) == today
        )
    )
    sent_result = await session.execute(sent_stmt)
    if sent_result.scalars().first():
        return False
    
    # Генерируем поздравление
    message_text = (
        f"🎉 С днём рождения, {user.full_name}!\n\n"
        f"Спасибо, что выбираете «Маунт»! Дарим вам промокод BIRTHDAY15 на скидку 15%."
    )
    
    # Определяем платформу для отправки
    platform = None
    if user.telegram_id:
        platform = "telegram"
    elif user.vk_id:
        platform = "vk"
    elif user.max_id:
        platform = "max"
    
    if not platform or not platform_senders.get(platform):
        return False
    
    try:
        # Отправляем сообщение
        await platform_senders[platform](user_id, message_text)
        
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
        return True
    except Exception as e:
        print(f"Ошибка отправки поздравления: {e}")
        return False

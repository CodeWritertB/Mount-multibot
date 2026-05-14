from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Booking, Promocode, BirthdayMessage
from src.config import config
from datetime import date, datetime
import uuid

router = Router()


@router.message(Command("monitoring"))
async def cmd_monitoring(message: types.Message, session: AsyncSession):
    """
    Команда админа: /monitoring
    Показывает список броней на сегодня
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    stmt = select(Booking).where(Booking.booking_date == date.today())
    result = await session.execute(stmt)
    bookings = result.scalars().all()
    
    if not bookings:
        await message.answer("На сегодня броней нет.")
        return
        
    text = "📅 Брони на сегодня:\n\n"
    for b in bookings:
        text += (
            f"🔹 Стол: {b.table_id} | {b.start_time} - {b.end_time} | "
            f"{b.guests_count} чел. | Статус: {b.status}\n"
        )
        
    await message.answer(text)


@router.message(Command("promo_manager"))
async def cmd_promo_manager(message: types.Message, session: AsyncSession):
    """
    Команда админа: /promo_manager
    Управление промокодами
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    text = (
        "Управление промокодами:\n"
        "/create_promo [код] [значение] [тип] [макс_использований] - Создать промокод\n"
        "/list_promos - Список всех промокодов\n"
        "/delete_promo [id] - Удалить промокод"
    )
    await message.answer(text)


@router.message(Command("create_promo"))
async def cmd_create_promo(message: types.Message, session: AsyncSession):
    """
    Команда админа: /create_promo
    Создание нового промокода
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    try:
        parts = message.text.split()
        if len(parts) != 5:
            await message.answer(
                "Использование: /create_promo [код] [значение] [тип] [макс_использований]\n"
                "Пример: /create_promo jazz_night 15 percentage 100"
            )
            return

        code = parts[1]
        value = float(parts[2])
        promo_type = parts[3]
        max_uses = int(parts[4])

        from src.database.models import Promocode
        from sqlalchemy import insert

        stmt = insert(Promocode).values(
            code=code,
            discount_value=value,
            discount_type=promo_type,
            max_uses=max_uses,
            current_uses=0,
            valid_from=datetime.now(),
            valid_to=datetime.now().replace(year=datetime.now().year + 1),
            is_active=True
        )
        await session.execute(stmt)
        await session.commit()

        await message.answer(f"Промокод '{code}' создан!")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("list_promos"))
async def cmd_list_promos(message: types.Message, session: AsyncSession):
    """
    Команда админа: /list_promos
    Список всех промокодов
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    stmt = select(Promocode)
    result = await session.execute(stmt)
    promocodes = result.scalars().all()

    if not promocodes:
        await message.answer("Нет промокодов.")
        return

    text = "📋 Список промокодов:\n\n"
    for p in promocodes:
        text += (
            f"🔹 {p.code} | {p.discount_value} "
            f"{'%' if p.discount_type == 'percentage' else 'руб.'} | "
            f"Использовано: {p.current_uses}/{p.max_uses}\n"
        )

    await message.answer(text)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, session: AsyncSession):
    """
    Команда админа: /broadcast
    Создание рассылки
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    await message.answer(
        "Отправьте текст рассылки (можно с картинкой):\n"
        "Формат: [текст]\n[ссылка_на_картинку]"
    )


@router.message(Command("birthdays_today"))
async def cmd_birthdays_today(message: types.Message, session: AsyncSession):
    """
    Команда админа: /birthdays_today
    Список именинников сегодня
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    from sqlalchemy import func
    from src.database.models import User

    today = date.today()
    stmt = select(User).where(
        and_(
            func.extract('month', User.birth_date) == today.month,
            func.extract('day', User.birth_date) == today.day,
            User.is_banned == False
        )
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        await message.answer("Сегодня нет именинников.")
        return

    text = "🎉 Имянники сегодня:\n\n"
    for u in users:
        text += f"🔹 {u.full_name} | Телефон: {u.phone}\n"

    await message.answer(text)


@router.message(Command("send_birthday"))
async def cmd_send_birthday(message: types.Message, session: AsyncSession):
    """
    Команда админа: /send_birthday [user_id]
    Отправить поздравление вручную
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])
        from src.core.birthday import check_and_send_birthdays
        
        # Получаем пользователя
        from src.database.models import User
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            await message.answer("Пользователь не найден.")
            return

        # Отправляем поздравление
        from src.core.broadcast import platform_senders
        message_text = (
            f"🎉 С днём рождения, {user.full_name}!\n\n"
            f"Спасибо, что выбираете «Маунт»! Дарим вам промокод BIRTHDAY15 на скидку 15%."
        )

        if user.telegram_id and platform_senders["telegram"]:
            await platform_senders["telegram"](user.telegram_id, message_text)
            await message.answer(f"Поздравление отправлено пользователю {user.full_name}")
        else:
            await message.answer("Нет способа отправить поздравление.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("birthday_stats"))
async def cmd_birthday_stats(message: types.Message, session: AsyncSession):
    """
    Команда админа: /birthday_stats
    Статистика по поздравлениям
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    from sqlalchemy import func

    # Количество поздравлений за сегодня
    today = date.today()
    stmt = select(func.count(BirthdayMessage.id)).where(
        func.cast(BirthdayMessage.created_at, func.Date) == today
    )
    result = await session.execute(stmt)
    sent_today = result.scalar()

    # Всего поздравлений
    stmt = select(func.count(BirthdayMessage.id))
    result = await session.execute(stmt)
    total = result.scalar()

    await message.answer(
        f"📊 Статистика поздравлений:\n"
        f"Сегодня: {sent_today}\n"
        f"Всего: {total}"
    )


@router.message(Command("ban"))
async def cmd_ban(message: types.Message, session: AsyncSession):
    """
    Команда админа: /ban [user_id]
    Забанить пользователя
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])
        from src.database.models import User

        stmt = update(User).where(User.id == user_id).values(is_banned=True)
        await session.execute(stmt)
        await session.commit()

        await message.answer(f"Пользователь {user_id} забанен.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message, session: AsyncSession):
    """
    Команда админа: /unban [user_id]
    Разбанить пользователя
    """
    if message.from_user.id != config.TELEGRAM_ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])
        from src.database.models import User

        stmt = update(User).where(User.id == user_id).values(is_banned=False)
        await session.execute(stmt)
        await session.commit()

        await message.answer(f"Пользователь {user_id} разбанен.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

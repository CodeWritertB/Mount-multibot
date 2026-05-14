from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.booking import get_user_by_platform, create_user, get_available_tables, create_booking
from src.core.yookassa import create_payment_link
from src.telegram.states import RegistrationStates, BookingStates
from src.telegram.middleware import DbSessionMiddleware, CheckBanMiddleware
from datetime import datetime, timedelta, date, time
import uuid

router = Router()
# Применяем middleware ко всем сообщениям
router.message.middleware(DbSessionMiddleware())
router.message.middleware(CheckBanMiddleware())


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик команды /start
    Проверяет, зарегистрирован ли пользователь
    Если нет - начинает процесс регистрации
    """
    user = await get_user_by_platform(session, "telegram", message.from_user.id)
    if not user:
        await message.answer(
            "Добро пожаловать в «Маунт»! Для начала регистрации введите ваше ФИО:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        await message.answer(
            f"С возвращением, {user.full_name}!\n"
            "Используйте /book для бронирования стола."
        )


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Обработчик ввода ФИО при регистрации
    """
    await state.update_data(full_name=message.text)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Отправить контакт", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Теперь отправьте ваш номер телефона:", reply_markup=keyboard)
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик получения контакта при регистрации
    Создает нового пользователя в БД
    """
    data = await state.get_data()
    user = await create_user(
        session,
        full_name=data["full_name"],
        phone=message.contact.phone_number,
        platform="telegram",
        platform_id=message.from_user.id
    )
    await message.answer(
        f"Регистрация завершена! Теперь вы можете забронировать стол с помощью /book",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


@router.message(Command("book"))
async def cmd_book(message: types.Message, state: FSMContext):
    """
    Обработчик команды /book - начало процесса бронирования
    """
    await message.answer("Введите дату бронирования (ГГГГ-ММ-ДД):")
    await state.set_state(BookingStates.waiting_for_date)


@router.message(BookingStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    """
    Обработчик ввода даты бронирования
    Проверяет корректность даты и что она в будущем
    """
    try:
        booking_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        if booking_date < date.today():
            raise ValueError
        await state.update_data(booking_date=message.text)
        await message.answer("Введите время начала (ЧЧ:ММ):")
        await state.set_state(BookingStates.waiting_for_time)
    except ValueError:
        await message.answer(
            "Некорректная дата. Пожалуйста, используйте формат ГГГГ-ММ-ДД и выбирайте будущие даты."
        )


@router.message(BookingStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    """
    Обработчик ввода времени начала
    """
    try:
        start_time = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(start_time=message.text)
        await message.answer("Введите количество гостей:")
        await state.set_state(BookingStates.waiting_for_guests)
    except ValueError:
        await message.answer("Некорректное время. Пожалуйста, используйте формат ЧЧ:ММ.")


@router.message(BookingStates.waiting_for_guests)
async def process_guests(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик ввода количества гостей
    Проверяет доступные столы и показывает список
    """
    try:
        guests_count = int(message.text)
        data = await state.get_data()
        booking_date = datetime.strptime(data["booking_date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        # По умолчанию бронь на 2 часа
        end_time = (datetime.combine(date.today(), start_time) + timedelta(hours=2)).time()
        
        tables = await get_available_tables(session, booking_date, start_time, end_time, guests_count)
        
        if not tables:
            await message.answer(
                "К сожалению, на это время нет свободных столов. Попробуйте другую дату или время."
            )
            await state.clear()
            return
            
        await state.update_data(guests_count=guests_count, end_time=str(end_time))
        
        builder = InlineKeyboardBuilder()
        for table in tables:
            builder.button(
                text=f"{table.name} (до {table.capacity} чел.)",
                callback_data=f"table_{table.id}"
            )
        builder.adjust(1)
        
        await message.answer("Выберите стол:", reply_markup=builder.as_markup())
        await state.set_state(BookingStates.waiting_for_table)
    except ValueError:
        await message.answer("Пожалуйста, введите число.")


@router.callback_query(BookingStates.waiting_for_table, F.data.startswith("table_"))
async def process_table(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Обработчик выбора стола
    Создает бронь и генерирует ссылку для оплаты
    """
    table_id = uuid.UUID(callback.data.split("_")[1])
    data = await state.get_data()
    user = await get_user_by_platform(session, "telegram", callback.from_user.id)
    
    booking_date = datetime.strptime(data["booking_date"], "%Y-%m-%d").date()
    start_time = datetime.strptime(data["start_time"], "%H:%M").time()
    end_time = datetime.strptime(data["end_time"], "%H:%M").time()
    
    # Расчет суммы: 1000 руб. за 2 часа (заглушка)
    deposit_amount = 1000.0
    
    booking = await create_booking(
        session,
        user.id,
        table_id,
        booking_date,
        start_time,
        end_time,
        data["guests_count"],
        deposit_amount
    )
    
    pay_url, payment_id = await create_payment_link(
        booking.id, deposit_amount, "Бронь стола в Маунт"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", url=pay_url)
    
    await callback.message.edit_text(
        f"Бронирование создано!\n"
        f"Стол: {table_id}\n"
        f"Дата: {booking_date}\n"
        f"Время: {start_time}\n"
        f"Сумма депозита: {deposit_amount} руб.\n\n"
        "Для подтверждения оплатите депозит по ссылке ниже:",
        reply_markup=builder.as_markup()
    )
    await state.clear()


@router.message(Command("promo"))
async def cmd_promo(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик команды /promo - ввод промокода
    """
    await message.answer("Введите промокод:")
    await state.set_state(BookingStates.waiting_for_promo)


@router.message(BookingStates.waiting_for_promo)
async def process_promo(message: types.Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик ввода промокода
    Проверяет валидность и применяет скидку
    """
    from src.core.promo import validate_promo
    
    code = message.text.strip()
    promo = await validate_promo(session, code, "telegram")
    
    if not promo:
        await message.answer("Промокод не найден или недействителен.")
        await state.clear()
        return
    
    await state.update_data(promo_code=code, promo_id=str(promo.id))
    await message.answer(
        f"Промокод применен! Скидка: {promo.discount_value} "
        f"{'%' if promo.discount_type == 'percentage' else 'руб.'}"
    )
    await state.clear()

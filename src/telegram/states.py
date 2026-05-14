from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    """Состояния для процесса бронирования"""
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_guests = State()
    waiting_for_table = State()
    waiting_for_promo = State()
    waiting_for_payment = State()


class RegistrationStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    waiting_for_name = State()
    waiting_for_phone = State()

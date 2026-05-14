import uuid
from yookassa import Configuration, Payment
from src.config import config

# Настройка ЮKassa
Configuration.account_id = config.YOOKASSA_SHOP_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY.get_secret_value()


async def create_payment_link(
    booking_id: uuid.UUID,
    amount: float,
    description: str
) -> tuple:
    """
    Создание платежа через ЮKassa и получение ссылки для оплаты
    
    :param booking_id: ID бронирования
    :param amount: Сумма платежа
    :param description: Описание платежа
    :return: Кортеж (ссылка для оплаты, ID платежа)
    """
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": config.WEBHOOK_URL
        },
        "capture": True,
        "description": description,
        "metadata": {
            "booking_id": str(booking_id)
        }
    })
    
    return payment.confirmation.confirmation_url, payment.id


async def check_payment_status(payment_id: str) -> str:
    """
    Проверка статуса платежа
    
    :param payment_id: ID платежа в ЮKassa
    :return: Статус платежа
    """
    payment = Payment.find_one(payment_id)
    return payment.status


async def refund_payment(payment_id: str, amount: float) -> bool:
    """
    Возврат платежа
    
    :param payment_id: ID платежа
    :param amount: Сумма возврата
    :return: True если возврат успешен
    """
    try:
        refund = Payment.refund({
            "payment_id": payment_id,
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            }
        })
        return refund.status == "succeeded"
    except Exception:
        return False

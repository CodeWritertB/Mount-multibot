import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """
    Модель пользователя
    
    Один пользователь может быть привязан к нескольким платформам
    через telegram_id, vk_id, max_id
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    vk_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    max_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    social_links: Mapped[dict] = mapped_column(JSONB, default={})

    # Связи
    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")
    admin_logs: Mapped[List["AdminLog"]] = relationship(back_populates="admin")
    birthday_messages: Mapped[List["BirthdayMessage"]] = relationship(back_populates="user")


class Table(Base):
    """
    Модель стола в заведении
    """
    __tablename__ = "tables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    capacity: Mapped[int] = mapped_column(Integer)
    price_per_hour: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    bookings: Mapped[List["Booking"]] = relationship(back_populates="table")


class Booking(Base):
    """
    Модель бронирования стола
    
    Все бронирования хранятся в одной таблице, независимо от платформы
    """
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id"))
    booking_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    guests_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, confirmed, paid, cancelled
    deposit_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    yookassa_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Связи
    user: Mapped["User"] = relationship(back_populates="bookings")
    table: Mapped["Table"] = relationship(back_populates="tables")
    promocodes: Mapped[List["BookingPromocode"]] = relationship(back_populates="booking")


class Promocode(Base):
    """
    Модель промокода
    
    Может быть ограничен по платформе
    """
    __tablename__ = "promocodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    discount_type: Mapped[str] = mapped_column(String(10))  # percentage, fixed
    discount_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    max_uses: Mapped[int] = mapped_column(Integer, default=0)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    valid_from: Mapped[datetime] = mapped_column(DateTime)
    valid_to: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    platform: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # telegram, vk, max, null = all


class BookingPromocode(Base):
    """
    Модель связи бронирования и промокода
    
    Хранит историю применения промокодов
    """
    __tablename__ = "booking_promocodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"))
    promocode_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("promocodes.id"))
    discount_applied: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))

    # Связи
    booking: Mapped["Booking"] = relationship(back_populates="promocodes")


class AdminLog(Base):
    """
    Модель логов действий администратора
    
    Все действия сохраняются в единой таблице с указанием платформы
    """
    __tablename__ = "admin_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSONB, default={})
    platform: Mapped[str] = mapped_column(String(10))  # telegram, vk, max
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    admin: Mapped["User"] = relationship(back_populates="admin_logs")


class BirthdayMessage(Base):
    """
    Модель истории поздравлений с днём рождения
    
    Отслеживает отправку поздравлений
    """
    __tablename__ = "birthday_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    message_text: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, failed
    platform: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # telegram, vk, max
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связи
    user: Mapped["User"] = relationship(back_populates="birthday_messages")

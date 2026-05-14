# Маунт - Многоплатформенный бот для заведения

Многоплатформенный бот для автоматизации бронирования, оплаты и маркетинга в заведении «Маунт».

## Поддерживаемые платформы

- **Telegram** (aiogram 3.x)
- **VK** (vkbottle)
- **Max** (max-api)

## Функционал

- Бронирование столов с выбором даты, времени и количества гостей
- Интеграция с ЮKassa для онлайн-оплаты
- Промокоды и система лояльности
- Маркетинговые рассылки по базе пользователей
- Автоматические поздравления с днём рождения
- Админ-панель для управления ботом

## Технологии

- **Backend:** Python 3.11+
- **Telegram:** aiogram 3.x
- **VK:** vkbottle
- **Max:** max-api
- **Database:** PostgreSQL 15+ (единая для всех платформ)
- **ORM:** SQLAlchemy 2.0
- **Cache & FSM:** Redis 7+
- **Payment:** ЮKassa API
- **Deployment:** Docker + Docker Compose

## Архитектура

Проект построен по принципу **единое ядро, адаптивные интерфейсы**:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │     │    VK       │     │     Max     │
│  (aiogram)  │     │ (vkbottle)  │     │  (max-api)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └─────────┬─────────┘                   │
                 │                             │
         ┌───────▼───────┐                     │
         │  Shared Core  │                     │
         │  (Business    │                     │
         │   Logic)      │                     │
         └───────┬───────┘                     │
                 │                             │
    ┌────────────┴────────────┐                │
    │                         │                │
┌───▼────┐               ┌────▼─────┐     ┌────▼─────┐
│ Redis  │               │PostgreSQL│     │  Max DB  │
│ (FSM)  │               │  (Data)  │     │  (Cache) │
└────────┘               └──────────┘     └──────────┘
```

## Установка

### Локально

1. Клонируйте репозиторий
2. Создайте `.env` файл на основе `.env.example` и заполните переменные:
   ```bash
   cp .env.example .env
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите миграции базы данных:
   ```bash
   alembic upgrade head
   ```
5. Запустите бота:
   ```bash
   python src/main.py
   ```

### Docker

1. Скопируйте `.env.example` в `.env` и заполните переменные
2. Запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

### Установка PostgreSQL (если Docker не используется)

#### Windows:
1. Скачайте PostgreSQL с [официального сайта](https://www.postgresql.org/download/windows/)
2. Установите с паролем `pass`
3. Создайте базу данных `maunt`
4. Обновите `DATABASE_URL` в `.env` файле

#### macOS:
```bash
brew install postgresql
brew services start postgresql
createuser -s user
createdb maunt
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser -s user
sudo -u postgres createdb maunt
```

## Структура проекта

```
maunt-bot/
├── src/
│   ├── __init__.py
│   ├── config.py                 # Конфигурация приложения
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy модели (единая БД)
│   │   └── session.py            # Сессия БД
│   ├── redis/
│   │   ├── __init__.py
│   │   └── client.py             # Redis клиент (общий для всех платформ)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── booking.py            # Общая логика бронирования
│   │   ├── promo.py              # Общая логика промокодов
│   │   ├── broadcast.py          # Общая логика рассылок
│   │   ├── birthday.py           # Общая логика поздравлений
│   │   ├── yookassa.py           # Интеграция с ЮKassa
│   │   └── webhooks.py           # Webhook обработчики
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── telegram.py           # Адаптер Telegram
│   │   ├── vk.py                 # Адаптер VK
│   │   └── max.py                # Адаптер Max
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── handlers.py           # Обработчики команд (адаптер)
│   │   ├── states.py             # FSM состояния (адаптер)
│   │   └── middleware.py         # Middleware (адаптер)
│   ├── vk/
│   │   ├── __init__.py
│   │   ├── handlers.py           # Обработчики команд (адаптер)
│   │   └── states.py             # FSM состояния (адаптер)
│   ├── max/
│   │   ├── __init__.py
│   │   ├── handlers.py           # Обработчики команд (адаптер)
│   │   └── states.py             # FSM состояния (адаптер)
│   ├── admin/
│   │   ├── __init__.py
│   │   └── handlers.py           # Админ-команды
│   └── main.py                   # Точка входа (запуск всех платформ)
├── migrations/                   # Alembic миграции
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

## Переменные окружения

См. `.env.example` для списка необходимых переменных.

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота |
| `TELEGRAM_ADMIN_ID` | ID администратора в Telegram |
| `VK_GROUP_ID` | ID группы VK |
| `VK_API_SECRET` | Секретный ключ VK API |
| `DATABASE_URL` | URL подключения к PostgreSQL |
| `REDIS_URL` | URL подключения к Redis |
| `YOOKASSA_SHOP_ID` | ID магазина ЮKassa |
| `YOOKASSA_SECRET_KEY` | Секретный ключ ЮKassa |
| `YOOKASSA_WEBHOOK_SECRET` | Секрет для webhook ЮKassa |
| `WEBHOOK_URL` | URL для webhook от ЮKassa |

## Админ-команды

- `/monitoring` - брони на сегодня
- `/promo_manager` - управление промокодами
- `/create_promo [код] [значение] [тип] [макс_использований]` - создать промокод
- `/list_promos` - список всех промокодов
- `/broadcast` - создание рассылки
- `/birthdays_today` - список именинников сегодня
- `/send_birthday [user_id]` - отправить поздравление вручную
- `/birthday_stats` - статистика по поздравлениям
- `/ban [user_id]` - забанить пользователя
- `/unban [user_id]` - разбанить пользова��еля

## Примеры использования

### Бронирование стола (для пользователя)

1. Отправьте `/start` в Telegram боте
2. Пройдите регистрацию (ФИО + номер телефона)
3. Отправьте `/book`
4. Следуйте инструкциям: дата → время → количество гостей → выбор стола
5. Оплатите депозит по ссылке из ЮKassa

### Создание промокода (для админа)

```
/create_promo jazz_night 15 percentage 100
```

Создаст промокод `jazz_night` с 15% скидкой, максимальным количеством использований 100.

## Лицензия

MIT
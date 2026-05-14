from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """
    Класс настроек приложения
    
    Загружает переменные из .env файла
    """
    # Telegram
    TELEGRAM_BOT_TOKEN: SecretStr
    TELEGRAM_ADMIN_ID: int

    # VK
    VK_GROUP_ID: int
    VK_API_SECRET: SecretStr

    # Database
    DATABASE_URL: PostgresDsn

    # Redis
    REDIS_URL: RedisDsn

    # ЮKassa
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: SecretStr
    YOOKASSA_WEBHOOK_SECRET: SecretStr

    # Webhook
    WEBHOOK_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Создание экземпляра настроек
config = Settings()

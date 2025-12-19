from typing import List
import os
import dj_database_url
from pydantic_settings import BaseSettings


class EventSettings(BaseSettings):
    # debug
    DEBUG: bool = True

    # group id
    GROUP_ID: int = 4817936909

    # secret
    SECRET_KEY: str = "django-insecure-demo=secret"

    # db url
    DB_URL: str = "sqlite:///db.sqlite3"

    # project
    PROJECT_URL: str = "http://localhost:8000"

    # eskiz
    ESKIZ_HOST: str = ""
    ESKIZ_EMAIL: str = ""
    ESKIZ_PASSWORD: str = ""

    # redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # passenger / driver
    PASSENGER_BOT_URL: str = "http://localhost:8888"
    DRIVER_BOT_URL: str = "http://localhost:8080"

    # Telegram bot token (.env yoki environment'dan olinadi)
    MAIN_BOT: str = ""

    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        hosts = [
            '127.0.0.1',
            "0.0.0.0",
            'localhost',
            'goz-dev.uz',
            self.PROJECT_URL,
            self.DRIVER_BOT_URL,
            self.PASSENGER_BOT_URL,
        ]
        # Environment'dan qo'shimcha hostlar
        extra_hosts = os.getenv('ALLOWED_HOSTS', '')
        if extra_hosts:
            hosts.extend(extra_hosts.split(','))
        return hosts

    @property
    def DATABASES(self):
        """Django DATABASES sozlamasi"""
        return {
            'default': dj_database_url.config(
                default=self.DB_URL,
                conn_max_age=600,
                ssl_require=False
            )
        }

    class Config:
        # Bir nechta .env fayllarini tekshirish
        env_file = [
            ".env",                    # Joriy papkada
            "deploy/.env",            # deploy papkasida
            "/app/.env",              # Docker container ichida
            "/var/www/event/goz-base-server/.env"  # Serverdagi asosiy papka
        ]
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Qo'shimcha field'larga ruxsat


def en():
    """Environment settings olish"""
    try:
        return EventSettings()
    except Exception as e:
        print(f"⚠️ Settings load error: {e}")
        # Default sozlamalar bilan ishga tushirish
        return EventSettings(_env_file=None)


env = en()

# Debug uchun print (faqat development'da)
if env.DEBUG:
    print(f"✅ Settings loaded: MAIN_BOT={'***' if env.MAIN_BOT else 'Not set'}")
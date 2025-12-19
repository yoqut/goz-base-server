from typing import List

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

    MAIN_BOT: str = None

    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return [
            '127.0.0.1',
            "0.0.0.0",
            self.PROJECT_URL,
            self.DRIVER_BOT_URL,
            self.PASSENGER_BOT_URL,
        ]

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
        env_file = "deploy/.env"


def en():
    return EventSettings()


env = en()

# psql -h database-1.czic202o6e4s.eu-north-1.rds.amazonaws.com -U postgres -d postgres database connection

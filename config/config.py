from dataclasses import dataclass
from environs import *

@dataclass
class DatabaseConfig:
    database: str         # Название базы данных
    db_host: str          # URL-адрес базы данных
    db_user: str          # Username пользователя базы данных
    db_password: str      # Пароль к базе данных
    db_port: str          # Порт базы данных


@dataclass
class MaxBot:
    token: str            # Токен для доступа к боту


@dataclass
class Config:
    Max_bot: MaxBot
    db: DatabaseConfig


def load_config(path: str | None = None) -> Config:
    # Создаем экземпляр класса Env
    env: Env = Env()
    # Добавляем в переменные окружения данные, прочитанные из файла .env
    env.read_env()

    # Создаем экземпляр класса Config и наполняем его данными из переменных окружения
    return Config(
        Max_bot=MaxBot(
            token=env('BOT_TOKEN'),

        ),
        db=DatabaseConfig(
            database=env('DATABASE'),
            db_host=env('DB_HOST'),
            db_user=env('DB_USER'),
            db_password=env('DB_PASSWORD'),
            db_port=env('PORT')
        ),
        )

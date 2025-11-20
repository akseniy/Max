import asyncio
import logging

from maxapi import Bot, Dispatcher
from config.config import Config, load_config
from handlers.handlers import base_router
import asyncpg


async def init_database(pool):
    """Инициализирует базу данных - создает таблицы если их нет"""
    try:
        async with pool.acquire() as conn:
            # Создаем последовательность
            await conn.execute('''
                CREATE SEQUENCE IF NOT EXISTS group_id_seq
                    START WITH 37
                    INCREMENT BY 17
                    NO MINVALUE
                    NO MAXVALUE
                    CACHE 1;
            ''')
            
            # Создаем таблицы
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "users" (
                    id BIGINT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT now()
                );
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "group" (
                    id INTEGER PRIMARY KEY DEFAULT nextval('group_id_seq'),
                    name TEXT NOT NULL
                );
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_group (
                    fk_user_id BIGINT NOT NULL,
                    fk_group_id INTEGER NOT NULL,
                    PRIMARY KEY (fk_user_id, fk_group_id),
                    CONSTRAINT fk_user FOREIGN KEY (fk_user_id) REFERENCES "users"(id) ON DELETE CASCADE,
                    CONSTRAINT fk_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
                );
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admin (
                    fk_user_id BIGINT NOT NULL,
                    fk_group_id INTEGER NOT NULL,
                    PRIMARY KEY (fk_user_id, fk_group_id),
                    CONSTRAINT fk_admin_user FOREIGN KEY (fk_user_id) REFERENCES "users"(id) ON DELETE CASCADE,
                    CONSTRAINT fk_admin_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
                );
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS event (
                    id SERIAL PRIMARY KEY,
                    fk_group_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_start TEXT NOT NULL,
                    time_end TEXT NOT NULL,
                    CONSTRAINT fk_event_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
                );
            ''')
            
            print("✅ База данных инициализирована - таблицы созданы/проверены")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        raise


async def create_pool_with_retry(config, retries=10, delay=3):
    """Создаём подключение к базе с повторными попытками"""
    for i in range(retries):
        try:
            pool = await asyncpg.create_pool(
                user=config.db.db_user,
                password=config.db.db_password,
                database=config.db.database,
                host=config.db.db_host,
                port=config.db.db_port
            )
            print("✅ Подключение к базе успешно")
            return pool
        except Exception as e:
            print(f"⚠️ База данных не готова, попытка {i+1}/{retries}...")
            await asyncio.sleep(delay)
    raise Exception("❌ Не удалось подключиться к базе после нескольких попыток")



async def main():
    logging.basicConfig(level=logging.INFO, filename='py_log.log', filemode='w')

    # Загружаем конфиг
    config: Config = load_config()

    # Инициализируем бота и диспетчер
    bot = Bot(token=config.Max_bot.token)
    main_dp = Dispatcher()

    # Подключаемся к базе с повторными попытками
    pool = await create_pool_with_retry(config)
    bot.pool = pool

    # Регистрируем роутеры
    main_dp.include_routers(base_router)

    # Запуск polling
    await main_dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

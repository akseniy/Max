import asyncio
import logging

from maxapi import Bot, Dispatcher
from config.config import Config, load_config
from handlers.handlers import base_router
import asyncpg


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

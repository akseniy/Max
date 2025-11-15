import asyncio
import logging


from maxapi import Bot, Dispatcher



from config.config import Config, load_config
from handlers.handlers import base_router
from asyncpg import create_pool



async def main():
    logging.basicConfig(level=logging.INFO, filename='py_log.log', filemode='w')

    # Загружаем конфиг в переменную config
    config: Config = load_config()


    # Инициализируем бот, диспетчер, redis и коннект к базе данных
    bot = Bot(token=config.Max_bot.token)
    main_dp = Dispatcher()
    pool = await create_pool(user=config.db.db_user, database=config.db.database, host=config.db.db_host, port=config.db.db_port)




    # Добавляем пул для общей видимости по проекту
    main_dp.workflow_data.update({'pool': pool})



    # Регистриуем роутеры на диспетчере для основного бота
    main_dp.include_routers(base_router)


    await main_dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
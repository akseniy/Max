from keyboards.keyboards import menu_kb, help_kb, groups_kb, my_groups_kb
from lexicon.lexicon import lexicon
from config.config import Config, load_config
from asyncpg import create_pool


from fsm.fsm import Form
from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback
from maxapi.context import MemoryContext, State, StatesGroup


base_router = Router()


# Загружаем конфиг в переменную config
config: Config = load_config()

@base_router.message_created(F.message.body.text=='/start')
async def start(event: MessageCreated, context: MemoryContext):
    await event.message.answer(text=lexicon['hello_message'], attachments=[menu_kb.as_markup()])
    await context.clear()


@base_router.message_callback(F.callback.payload == 'menu')
async def message_callback_menu(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer(text=lexicon['menu_message'], attachments=[menu_kb.as_markup()])
    await context.set_state(Form.menu)


@base_router.message_callback(F.callback.payload == 'help')
async def message_callback_help(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer(text=lexicon['help_message'], attachments=[help_kb.as_markup()])
    await context.set_state(Form.help)


@base_router.message_callback(F.callback.payload == 'groups')
async def message_callback_groups(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer(text=lexicon['group_message'], attachments=[groups_kb.as_markup()])
    await context.set_state(Form.groups)


@base_router.message_callback(F.callback.payload == 'my_groups')
async def message_callback_groups(callback: MessageCallback, context: MemoryContext, pool):
    async with pool.acquire() as conn:
            await conn.execute("UPDATE cities SET city = $1 WHERE user_id = $2", city, str(user_id))
    await callback.message.answer(text=lexicon['group_message'], attachments=[my_groups_kb.as_markup()])
    await context.set_state(Form.my_groups)

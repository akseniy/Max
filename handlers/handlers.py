from keyboards.keyboards import menu_kb, help_kb, groups_kb, my_groups_kb, admin_groups_kb
from lexicon.lexicon import lexicon
from config.config import Config, load_config
from asyncpg import create_pool
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


from fsm.fsm import Form
from maxapi import Router, F, Bot
from maxapi.types import MessageCreated, MessageCallback, BotStarted
from maxapi.context import MemoryContext, State, StatesGroup


base_router = Router()


# Загружаем конфиг в переменную config
config: Config = load_config()

@base_router.bot_started()
async def bot_started(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text='Привет! Отправь мне /start'
    )
    data = event.message.sender
    pool = event.bot.pool
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users VALUES ($1, $2, $3)", data.user_id, data.first_name, data.last_name)


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
async def message_callback_help(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer(text=lexicon['group_message'], attachments=[groups_kb.as_markup()])
    await context.set_state(Form.help)



# Кнопки для действий с группами
def group_action_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(text="Вступить в группу", payload="join_group"),
        CallbackButton(text="Выйти из группы", payload="leave_group")
    )
    return kb


# 1. Показ списка групп
@base_router.message_callback(F.callback.payload == 'my_groups')
async def show_user_groups(callback: MessageCallback, context: MemoryContext):
    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT "group".id, "group".name
            FROM "group"
            JOIN user_group ON user_group.fk_group_id = "group".id
            WHERE user_group.fk_user_id = $1
            """,
            int(user_id)
        )

    if not rows:
        text = "У вас нет групп."
    else:
        text_lines = [f"{i+1}. {r['name']} (ID: {r['id']})" for i, r in enumerate(rows)]
        text = "Ваши группы:\n" + "\n".join(text_lines)

    await callback.message.answer(text=text, attachments=[group_action_kb().as_markup()])
    await context.set_state(Form.groups)

# 2. Вступление в группу по коду
@base_router.message_callback(F.callback.payload == 'join_group')
async def join_group(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer("Введите пригласительный код группы:")
    await context.set_state(Form.join_to_group)

@base_router.message_created(F.message.body.text, Form.join_to_group)
async def join_group_process(event: MessageCreated, context: MemoryContext):
    pool = event.bot.pool
    user_id = event.message.sender.user_id
    code_str = event.message.body.text.strip()

    try:
        code = int(code_str)
    except ValueError:
        await event.message.answer("❌ Код группы должен быть числом.", attachments=[menu_kb.as_markup()])
        await context.set_state(Form.menu)
        return

    async with pool.acquire() as conn:
        group = await conn.fetchrow('SELECT id FROM "group" WHERE id = $1', code)
        if group is None:
            await event.message.answer("❌ Группа с таким кодом не найдена.", attachments=[menu_kb.as_markup()])
        else:
            await conn.execute(
                """
                INSERT INTO user_group (fk_user_id, fk_group_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                user_id,
                group["id"]
            )
            await event.message.answer(f"✅ Вы успешно вступили в группу {group['id']}.", attachments=[menu_kb.as_markup()])

    await context.set_state(Form.menu)

# 3. Удаление пользователя из группы
@base_router.message_callback(F.callback.payload == 'leave_group')
async def leave_group(callback: MessageCallback, context: MemoryContext):
    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT g.id, g.name
            FROM "group" g
            JOIN user_group ug ON ug.fk_group_id = g.id
            WHERE ug.fk_user_id = $1
            """,
            user_id
        )

    if not rows:
        await callback.message.answer("У вас нет групп для выхода.", attachments=[menu_kb.as_markup()])
        await context.set_state(Form.menu)
        return


    text_lines = [f"{i+1}. {r['name']}" for i, r in enumerate(rows)]
    await callback.message.answer("Выберите номер группы для выхода:\n" + "\n".join(text_lines))
    await context.set_state(Form.exit_the_group)


@base_router.message_created(F.message.body.text, Form.exit_the_group)
async def leave_group_process(event: MessageCreated, context: MemoryContext):
    pool = event.bot.pool
    user_id = event.message.sender.user_id
    num_str = event.message.body.text.strip()
    try:
        num = int(num_str)
    except ValueError:
        await event.message.answer("❌ Введите корректный номер.", attachments=[menu_kb.as_markup()])
        await context.set_state(Form.menu)
        return
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT g.id, g.name
            FROM "group" g
            JOIN user_group ug ON ug.fk_group_id = g.id
            WHERE ug.fk_user_id = $1
            """,
            user_id
        )
    groups_list = rows
    if num < 1 or num > len(groups_list):
        await event.message.answer("❌ Неверный номер группы.", attachments=[menu_kb.as_markup()])
        await context.set_state(Form.menu)
        return

    group_to_leave = groups_list[num - 1]

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM user_group WHERE fk_user_id=$1 AND fk_group_id=$2",
            user_id,
            group_to_leave['id']
        )

    await event.message.answer(f"✅ Вы вышли из группы {group_to_leave['name']}.", attachments=[menu_kb.as_markup()])
    await context.set_state(Form.menu)


@base_router.message_callback(F.callback.payload == 'my_groups')
async def message_callback_my_groups(callback: MessageCallback, context: MemoryContext):
    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT "group".name AS group_name
            FROM "group"
            JOIN user_group ON user_group.fk_group_id = "group".id
            WHERE user_group.fk_user_id = $1
            """,
            int(user_id)
        )

    if not rows:
        await callback.message.answer("У вас нет групп.")
        await callback.message.answer(text=lexicon['menu_message'], attachments=[menu_kb.as_markup()])
        await context.set_state(Form.menu)
        return

    # Формируем текст списка групп
    text = "\n".join([f"{i+1}. {r['group_name']}" for i, r in enumerate(rows)])
    await callback.message.answer("Ваши группы:\n\n" + text)

    # Добавляем инлайн кнопки для действий по каждой группе
    kb = InlineKeyboardBuilder()
    for i, r in enumerate(rows, start=1):
        kb.row(CallbackButton(text=f"Добавить событие ({r['group_name']})", payload=f"add_event:{i}"))
        kb.row(CallbackButton(text=f"Удалить событие ({r['group_name']})", payload=f"del_event:{i}"))

    # Кнопка назад
    kb.row(CallbackButton(text="⬅️ Назад", payload="menu"))

    await callback.message.answer(text="Выберите действие:", attachments=[kb.as_markup()])
    await context.set_state(Form.my_groups)



@base_router.message_callback(F.callback.payload == 'admin_groups')
async def message_callback_admin_groups(callback: MessageCallback, context: MemoryContext):


    pool = callback.bot.pool
    async with pool.acquire() as conn:
            user_id = callback.message.recipient.user_id
            rows = await conn.fetch(
                    """
                    SELECT "group".name
                    FROM "group"
                    INNER JOIN "admin" ON "admin".fk_group_id= "group".id
                    WHERE "admin".fk_user_id = $1
                    """,
                    int(user_id)
                )

    await callback.message.answer(text=lexicon['group_message'], attachments=[admin_groups_kb.as_markup()])
    await context.set_state(Form.my_groups)


@base_router.message_callback(F.callback.payload == 'create_the_group')
async def message_callback_create_the_group(callback: MessageCallback, context: MemoryContext):

    await callback.message.answer(text='Введите желаемое название')
    await context.set_state(Form.create_the_group)


@base_router.message_created(F.message.body.text, Form.create_the_group)
async def message_create_the_name(event: MessageCreated, context: MemoryContext):

    name = event.message.body.text
    user_id = event.message.sender.user_id

    pool = event.bot.pool
    async with pool.acquire() as conn:

        # 1. Создаём группу
        row = await conn.fetchrow(
            """
            INSERT INTO "group" (name)
            VALUES ($1)
            RETURNING id
            """,
            name
        )

        group_id = row["id"]

        # 2. Делаем создателя администратором
        await conn.execute(
            """
            INSERT INTO admin (fk_user_id, fk_group_id)
            VALUES ($1, $2)
            """,
            int(user_id),
            int(group_id)
        )

    # 3. Сообщение пользователю
    await event.message.answer(
        text=f"Группа создана!\nТвой код приглашения: {group_id}",
        attachments=[menu_kb.as_markup()]
    )

    await context.set_state(Form.menu)






@base_router.message_callback(F.callback.payload == 'create_an_event')
async def start_create_event(callback: MessageCallback, context: MemoryContext):

    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT g.id, g.name
            FROM "group" g
            JOIN admin a ON a.fk_group_id = g.id
            WHERE a.fk_user_id = $1
            """,
            int(user_id)
        )

    if not rows:
        await callback.message.answer("У вас нет групп, где вы являетесь админом.")
        return

    # Сохраняем группы в FSM
    groups = [(row['id'], row['name']) for row in rows]
    await context.update_data(admin_groups=groups)

    # Формируем красивый список
    text = "Выберите номер группы:\n\n"
    for i, g in enumerate(groups, start=1):
        text += f"{i}. {g[1]}\n"

    await callback.message.answer(text)
    await context.set_state(Form.create_event_choose_group)


@base_router.message_created(F.message.body.text, Form.create_event_choose_group)
async def choose_group(event: MessageCreated, context: MemoryContext):

    text = event.message.body.text

    if not text.isdigit():
        await event.message.answer("Введите номер, а не текст")
        return

    number = int(text)
    data = await context.get_data()

    groups = data['admin_groups']

    if number < 1 or number > len(groups):
        await event.message.answer("Неверный номер. Попробуйте снова.")
        return

    group_id = groups[number - 1][0]

    # сохраняем ID группы
    await context.update_data(group_id=group_id)

    await event.message.answer("Введите название события:")
    await context.set_state(Form.create_event_name)

@base_router.message_created(F.message.body.text, Form.create_event_name)
async def event_name(event: MessageCreated, context: MemoryContext):

    await context.update_data(event_name=event.message.body.text)
    await event.message.answer("Введите дату в формате ГГГГ-ММ-ДД:")
    await context.set_state(Form.create_event_date)

@base_router.message_created(F.message.body.text, Form.create_event_date)
async def event_date(event: MessageCreated, context: MemoryContext):

    date = event.message.body.text

    # проверка даты
    import datetime
    try:
        datetime.date.fromisoformat(date)
    except:
        await event.message.answer("Неверный формат даты. Пример: 2025-12-31")
        return

    await context.update_data(event_date=date)
    await event.message.answer("Введите время начала (ЧЧ:ММ):")
    await context.set_state(Form.create_event_start)


@base_router.message_created(F.message.body.text, Form.create_event_start)
async def event_start(event: MessageCreated, context: MemoryContext):

    time_start = event.message.body.text

    try:
        import datetime
        datetime.time.fromisoformat(time_start)
    except:
        await event.message.answer("Неверный формат. Пример: 14:30")
        return

    await context.update_data(time_start=time_start)
    await event.message.answer("Введите время конца (ЧЧ:ММ):")
    await context.set_state(Form.create_event_end)


@base_router.message_created(F.message.body.text, Form.create_event_end)
async def event_end(event: MessageCreated, context: MemoryContext):

    time_end = event.message.body.text

    try:
        import datetime
        datetime.time.fromisoformat(time_end)
    except:
        await event.message.answer("Неверный формат. Пример: 16:00")
        return

    data = await context.get_data()

    pool = event.bot.pool
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO event (fk_group_id, name, date, time_start, time_end)
            VALUES ($1, $2, $3, $4, $5)
            """,
            data["group_id"],
            data["event_name"],
            data["event_date"],
            data["time_start"],
            time_end
        )

    await event.message.answer("Событие успешно добавлено!", attachments=[menu_kb.as_markup()])
    await context.set_state(Form.menu)


@base_router.message_callback(F.callback.payload == 'delete_event')
async def delete_event_start(callback: MessageCallback, context: MemoryContext):
    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.name
            FROM "group" g
            JOIN admin a ON a.fk_group_id = g.id
            WHERE a.fk_user_id = $1
        """, int(user_id))

    if not rows:
        await callback.message.answer("У вас нет групп, где вы админ.")
        return

    groups = [{"id": r["id"], "name": r["name"]} for r in rows]
    await context.update_data(groups=groups)

    text = "\n".join([f"{i+1}. {g['name']}" for i, g in enumerate(groups)])
    await callback.message.answer("Ваши группы:\n\n" + text + "\n\nВведите номер группы:")

    await context.set_state(Form.delete_event_choose_group)


@base_router.message_created(F.message.body.text, Form.delete_event_choose_group)
async def delete_event_choose_group(event: MessageCreated, context: MemoryContext):
    data = await context.get_data()
    groups = data["groups"]

    try:
        num = int(event.message.body.text)
        if num < 1 or num > len(groups):
            raise ValueError
    except:
        await event.message.answer("Введите корректный номер группы!")
        return

    chosen_group = groups[num - 1]
    pool = event.bot.pool

    async with pool.acquire() as conn:
        events = await conn.fetch("""
            SELECT id, name, date, time_start
            FROM event
            WHERE fk_group_id = $1
            ORDER BY date, time_start
        """, chosen_group["id"])

    if not events:
        await event.message.answer("В этой группе нет событий.")
        await context.clear()
        return

    events = [dict(e) for e in events]

    #  сохраняем события в FSM
    await context.update_data(events=events)

    text = "\n".join([
        f"{i+1}. {e['name']} — {e['date']} {e['time_start']}"
        for i, e in enumerate(events)
    ])

    await event.message.answer(
        f"События группы «{chosen_group['name']}»:\n\n{text}\n\nВведите номер события:"
    )

    await context.set_state(Form.delete_event_choose_event)


@base_router.message_created(F.message.body.text, Form.delete_event_choose_event)
async def delete_event_choose_event(event: MessageCreated, context: MemoryContext):
    data = await context.get_data()
    events = data["events"]

    try:
        num = int(event.message.body.text)
        if num < 1 or num > len(events):
            raise ValueError
    except:
        await event.message.answer("Введите корректный номер события!")
        return

    event_to_delete = events[num - 1]

    pool = event.bot.pool
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM event WHERE id = $1", event_to_delete["id"])

    await event.message.answer(f"Событие «{event_to_delete['name']}» удалено.")
    await context.clear()




@base_router.message_callback(F.callback.payload == "schedule")
async def show_schedule(callback: MessageCallback, context: MemoryContext):

    pool = callback.bot.pool
    user_id = callback.message.recipient.user_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                e.name AS event_name,
                e.date AS date,
                e.time_start AS time_start,
                e.time_end AS time_end,
                g.name AS group_name
            FROM event e
            JOIN "group" g ON g.id = e.fk_group_id
            JOIN user_group ug ON ug.fk_group_id = g.id
            WHERE ug.fk_user_id = $1
            ORDER BY e.date::date, e.time_start::time
            """,
            int(user_id)
        )

    if not rows:
        await callback.message.answer("У вас пока нет событий.")
        return

    # Формирование комплексного расписания
    result = "📅 Ваше расписание событий:\n\n"

    for r in rows:
        result += f"📌 {r['event_name']}\n" + f"👥 Группа: {r['group_name']}\n" + f"📆 Дата: {r['date']}\n" + f"⏰ Время: {r['time_start']} — {r['time_end']}\n\n"



    await callback.message.answer(result, attachments=[help_kb.as_markup()])
    await context.set_state(Form.menu)


# Когда пользователь нажимает "Вступить в группу"
@base_router.message_callback(F.callback.payload == "join_to_group")
async def join_group_request(callback: MessageCallback, context: MemoryContext):
    await callback.message.answer("Введите пригласительный код группы:")
    await context.set_state(Form.join_to_group)


@base_router.message_created(F.message.body.text, Form.join_to_group)
async def join_group_process(event: MessageCreated, context: MemoryContext):
    pool = event.bot.pool
    user_id = event.message.sender.user_id
    code_str = event.message.body.text.strip()  # введённый код группы

    try:
        code = int(code_str)  # преобразуем в число
    except ValueError:
        await event.message.answer(
            "❌ Код группы должен быть числом.",
            attachments=[menu_kb.as_markup()]
        )
        await context.set_state(Form.menu)
        return

    async with pool.acquire() as conn:
        # Проверяем, существует ли группа с таким id
        group = await conn.fetchrow(
            "SELECT id FROM \"group\" WHERE id = $1",
            code
        )

        if group is None:
            await event.message.answer(
                "❌ Группа с таким кодом не найдена.",
                attachments=[menu_kb.as_markup()]
            )
        else:
            # Добавляем пользователя в группу
            await conn.execute(
                """
                INSERT INTO user_group (fk_user_id, fk_group_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                user_id,
                group["id"]
            )
            await event.message.answer(
                f"✅ Вы успешно вступили в группу с кодом {group['id']}.",
                attachments=[menu_kb.as_markup()]
            )

    await context.set_state(Form.menu)



@base_router.message_created(F.message.body.text)
async def other(event: MessageCreated, context: MemoryContext):
    await event.message.answer(text=lexicon['other_message'])
    context.clear()

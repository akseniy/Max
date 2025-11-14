from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


kb = InlineKeyboardBuilder()
kb.row(
            CallbackButton(text="Мои группы", payload="my_groups"),
            CallbackButton(text="Управление группами", payload="admin_groups")
        )

menu_kb = InlineKeyboardBuilder()
menu_kb.row(
    CallbackButton(text='Помощь', payload='help'),
    CallbackButton(text='Группы', payload='groups'),
    CallbackButton(text='Расписание', payload='schedule')
)

help_kb = InlineKeyboardBuilder()
help_kb.row(
    CallbackButton(text='В меню', payload='menu')
)

groups_kb = InlineKeyboardBuilder()
groups_kb.row(
    CallbackButton(text='Мои группы', payload='my_groups'),
    CallbackButton(text='Управление группами', payload='admin_groups')
)
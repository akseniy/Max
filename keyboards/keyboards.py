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

my_groups_kb = InlineKeyboardBuilder()
my_groups_kb.row(
    CallbackButton(text='Вступить в группу', payload='join_to_group'),
    CallbackButton(text='Покинуть группу', payload='exit_the_group')
)

admin_groups_kb = InlineKeyboardBuilder()
admin_groups_kb.row(CallbackButton(text='Удалить событие', payload='delete_event'))
admin_groups_kb.row(CallbackButton(text='Создать группу', payload='create_the_group'))
admin_groups_kb.row(CallbackButton(text='Добавить событие в группу', payload='create_an_event'))
admin_groups_kb.row(CallbackButton(text='Удалить группу', payload='delete_group'))

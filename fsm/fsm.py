from maxapi.context import State, StatesGroup


class Form(StatesGroup):
    menu = State()
    help = State()
    schedule = State()
    groups = State()
    my_groups = State()
    admin_groups = State()
    join_to_group = State()
    exit_the_group = State()
    create_the_group = State()
    create_an_event = State()
    delete_the_group = State()
    delete_user = State()
    delete_event = State()
    delete_user_number = State()
    delete_event_number = State()

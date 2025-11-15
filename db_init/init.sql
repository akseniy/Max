CREATE SEQUENCE group_id_seq
    START WITH 37
    INCREMENT BY 17
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

 -- Таблица пользователей
CREATE TABLE IF NOT EXISTS "users" (
    id BIGINT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Таблица групп
CREATE TABLE IF NOT EXISTS "group" (
    id INTEGER PRIMARY KEY DEFAULT nextval('group_id_seq'),
    name TEXT NOT NULL
);

-- Связь пользователя с группой
CREATE TABLE IF NOT EXISTS user_group (
    fk_user_id BIGINT NOT NULL,
    fk_group_id INTEGER NOT NULL,
    PRIMARY KEY (fk_user_id, fk_group_id),
    CONSTRAINT fk_user FOREIGN KEY (fk_user_id) REFERENCES "users"(id) ON DELETE CASCADE,
    CONSTRAINT fk_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
);

-- Таблица админов групп
CREATE TABLE IF NOT EXISTS admin (
    fk_user_id BIGINT NOT NULL,
    fk_group_id INTEGER NOT NULL,
    PRIMARY KEY (fk_user_id, fk_group_id),
    CONSTRAINT fk_admin_user FOREIGN KEY (fk_user_id) REFERENCES "users"(id) ON DELETE CASCADE,
    CONSTRAINT fk_admin_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
);

-- Таблица событий
CREATE TABLE IF NOT EXISTS event (
    id SERIAL PRIMARY KEY,
    fk_group_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time_start TEXT NOT NULL,
    time_end TEXT NOT NULL,
    CONSTRAINT fk_event_group FOREIGN KEY (fk_group_id) REFERENCES "group"(id) ON DELETE CASCADE
);
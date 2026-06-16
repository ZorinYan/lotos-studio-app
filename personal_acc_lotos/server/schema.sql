-- Схема PostgreSQL для Lotos (Supabase / Neon). Мини-app + VK-бот.
-- Таблицы уже созданы вручную; файл для справки и новых окружений.

CREATE TABLE IF NOT EXISTS users (
  vk_user_id            BIGINT PRIMARY KEY,
  phone                 VARCHAR(11) UNIQUE NOT NULL,
  client_name           TEXT,
  favorite_staff_id     INTEGER,
  favorite_staff_name   TEXT,
  last_booking          JSONB,
  notifications_enabled BOOLEAN DEFAULT FALSE,
  linked_at             TIMESTAMPTZ DEFAULT NOW(),
  auth_method           TEXT,
  password_hash         TEXT,
  logged_in             BOOLEAN DEFAULT FALSE,
  color_scheme          TEXT DEFAULT 'light',
  welcome_banner_seen   BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS reminder_log (
  id         BIGSERIAL PRIMARY KEY,
  vk_user_id BIGINT NOT NULL,
  kind       TEXT NOT NULL,
  entity_id  TEXT NOT NULL,
  sent_at    TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (vk_user_id, kind, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_reminder_log_entity
  ON reminder_log (kind, entity_id);

-- Аккаунты сотрудников студии (отдельно от клиентских users).
CREATE TABLE IF NOT EXISTS staff_accounts (
  phone                 VARCHAR(11) PRIMARY KEY,
  yclients_staff_id     INTEGER NOT NULL,
  yclients_user_id      INTEGER,
  staff_name            TEXT NOT NULL,
  specialization        TEXT,
  position_title        TEXT,
  vk_user_id            BIGINT,
  password_hash         TEXT,
  logged_in             BOOLEAN DEFAULT FALSE,
  color_scheme          TEXT DEFAULT 'light',
  linked_at             TIMESTAMPTZ DEFAULT NOW(),
  last_login_at         TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_accounts_yclients_staff_id
  ON staff_accounts (yclients_staff_id);

CREATE INDEX IF NOT EXISTS idx_staff_accounts_vk_user_id
  ON staff_accounts (vk_user_id);

-- Для уже созданной БД:
-- (выполнить вручную в Supabase SQL editor)
-- ALTER TABLE staff_accounts ADD COLUMN IF NOT EXISTS color_scheme TEXT DEFAULT 'light';

-- Для уже созданной таблицы users:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS logged_in BOOLEAN DEFAULT FALSE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS color_scheme TEXT DEFAULT 'light';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS welcome_banner_seen BOOLEAN DEFAULT FALSE;

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

-- Для уже созданной таблицы users:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS logged_in BOOLEAN DEFAULT FALSE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS color_scheme TEXT DEFAULT 'light';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS welcome_banner_seen BOOLEAN DEFAULT FALSE;

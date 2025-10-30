from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "events" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "google_event_id" VARCHAR(255) NOT NULL UNIQUE,
    "title" VARCHAR(500) NOT NULL,
    "description" TEXT NOT NULL,
    "start_time" TIMESTAMPTZ NOT NULL,
    "end_time" TIMESTAMPTZ NOT NULL,
    "location" VARCHAR(500),
    "status" VARCHAR(9) NOT NULL DEFAULT 'active',
    "reminder_intervals" JSONB NOT NULL,
    "poll_interval" INT NOT NULL DEFAULT 24,
    "deadline" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "events"."status" IS 'ACTIVE: active\nCANCELLED: cancelled\nPOSTPONED: postponed\nCOMPLETED: completed';
CREATE TABLE IF NOT EXISTS "event_notifications" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "notification_type" VARCHAR(9) NOT NULL,
    "sent_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "event_id" INT NOT NULL REFERENCES "events" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "event_notifications"."notification_type" IS 'NEW_EVENT: new_event\nCANCELLED: cancelled\nPOSTPONED: postponed\nREMINDER: reminder';
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "username" VARCHAR(255),
    "locale" VARCHAR(2),
    "role" VARCHAR(5) NOT NULL DEFAULT 'user',
    "is_approved" BOOL NOT NULL DEFAULT False,
    "is_banned" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "users"."role" IS 'USER: user\nADMIN: admin';
CREATE TABLE IF NOT EXISTS "event_participants" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "reaction" VARCHAR(9),
    "reacted_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "event_id" INT NOT NULL REFERENCES "events" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_event_parti_event_i_7fc653" UNIQUE ("event_id", "user_id")
);
COMMENT ON COLUMN "event_participants"."reaction" IS 'GOING: going\nNOT_GOING: not_going\nTHINKING: thinking';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """

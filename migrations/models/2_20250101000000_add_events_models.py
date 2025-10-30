from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "events" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "google_event_id" VARCHAR(255) NOT NULL UNIQUE,
            "title" VARCHAR(500) NOT NULL,
            "description" TEXT NOT NULL,
            "start_time" TIMESTAMPTZ NOT NULL,
            "end_time" TIMESTAMPTZ NOT NULL,
            "location" VARCHAR(500),
            "status" VARCHAR(20) NOT NULL DEFAULT 'active',
            "reminder_intervals" JSONB NOT NULL DEFAULT '[]',
            "poll_interval" INT NOT NULL DEFAULT 24,
            "deadline" TIMESTAMPTZ,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE "event_participants" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "event_id" INT NOT NULL REFERENCES "events" ("id") ON DELETE CASCADE,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
            "reaction" VARCHAR(20),
            "reacted_at" TIMESTAMPTZ,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE("event_id", "user_id")
        );
        
        CREATE TABLE "event_notifications" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "event_id" INT NOT NULL REFERENCES "events" ("id") ON DELETE CASCADE,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
            "notification_type" VARCHAR(50) NOT NULL,
            "sent_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "is_read" BOOLEAN NOT NULL DEFAULT FALSE
        );
        
        ALTER TABLE "users" ADD COLUMN "role" VARCHAR(10) NOT NULL DEFAULT 'user';
        ALTER TABLE "users" ADD COLUMN "is_approved" BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE "users" ADD COLUMN "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE "event_notifications";
        DROP TABLE "event_participants";
        DROP TABLE "events";
        ALTER TABLE "users" DROP COLUMN "role";
        ALTER TABLE "users" DROP COLUMN "is_approved";
        ALTER TABLE "users" DROP COLUMN "created_at";
    """

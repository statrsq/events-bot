from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "found_profiles" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "occupation" VARCHAR(255),
    "min_age" INT,
    "max_age" INT,
    "sex" VARCHAR(10),
    "avatar_file_id" VARCHAR(255),
    "raw_json" JSONB NOT NULL
);
COMMENT ON TABLE "found_profiles" IS 'Найденные профили ';
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "locale" VARCHAR(2)
);
CREATE TABLE IF NOT EXISTS "profile_search_queries" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "query" TEXT NOT NULL,
    "status" VARCHAR(12) NOT NULL DEFAULT 'not_executed',
    "found_count" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "profile_search_queries"."status" IS 'NOT_EXECUTED: not_executed\nEXECUTED: executed';
COMMENT ON TABLE "profile_search_queries" IS 'Запросы для поиска профилей ';
CREATE TABLE IF NOT EXISTS "search_parameters" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "city" VARCHAR(100) NOT NULL,
    "city_en" VARCHAR(100) NOT NULL,
    "min_age" SMALLINT NOT NULL,
    "max_age" SMALLINT NOT NULL,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_like_stats" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "likes_available" SMALLINT NOT NULL,
    "likes_used_total" SMALLINT NOT NULL DEFAULT 0,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_reports" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "language" VARCHAR(2) NOT NULL,
    "sex" VARCHAR(1) NOT NULL,
    "occupation" VARCHAR(255),
    "raw_json" JSONB,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "shown_profiles" (
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "found_profile_id" BIGINT NOT NULL REFERENCES "found_profiles" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_shown_profi_user_id_11493f" ON "shown_profiles" ("user_id", "found_profile_id");
CREATE TABLE IF NOT EXISTS "search_queries_found_profiles" (
    "profile_search_queries_id" BIGINT NOT NULL REFERENCES "profile_search_queries" ("id") ON DELETE CASCADE,
    "foundprofile_id" BIGINT NOT NULL REFERENCES "found_profiles" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_search_quer_profile_ee9bac" ON "search_queries_found_profiles" ("profile_search_queries_id", "foundprofile_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """

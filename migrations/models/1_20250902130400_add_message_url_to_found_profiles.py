from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "found_profiles" ADD "message_url" VARCHAR(150);
        ALTER TABLE "found_profiles" ADD "channel_url" VARCHAR(150);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "found_profiles" DROP COLUMN "message_url";
        ALTER TABLE "found_profiles" DROP COLUMN "channel_url";"""

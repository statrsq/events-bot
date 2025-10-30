from tortoise import Model, fields

from src.bot.misc.enums.user_role import UserRole


class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    name = fields.CharField(max_length=255)
    username = fields.CharField(max_length=255, null=True)
    locale = fields.CharField(max_length=2, null=True)
    role = fields.CharEnumField(UserRole, default=UserRole.USER)
    is_approved = fields.BooleanField(default=False)
    is_banned = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"[id:{self.telegram_id}] {self.name}"

    class Meta:
        table = "users"
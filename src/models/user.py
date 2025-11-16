from tortoise import fields
from tortoise.models import Model


class UserSettings(Model):
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField(unique=True, description="Telegram user ID")

    timezone = fields.CharField(max_length=50, default="UTC")
    default_reminder_times = fields.JSONField(default=lambda: ["15m", "1h"], description="Default reminder times")
    date_format = fields.CharField(max_length=20, default="%Y-%m-%d %H:%M")

    # Calendar settings
    # calendar_sync_enabled = fields.BooleanField(default=True)
    # last_calendar_sync = fields.DatetimeField(null=True)

    # Notification preferences
    reminder_notifications = fields.BooleanField(default=True)
    completion_notifications = fields.BooleanField(default=True)

    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_settings"

    def __str__(self) -> str:
        return f"UserSettings(user_id={self.user_id})"

import pytz
from datetime import datetime
from typing import List, Optional
from tortoise import fields
from tortoise.models import Model


class Event(Model):
    id = fields.IntField(pk=True)

    chat_id = fields.BigIntField(description="Telegram chat ID where event was created")
    message_id = fields.BigIntField(null=True, description="Pinned message ID in chat")
    bot_message_id = fields.BigIntField(null=True, description="Message ID in bot's private chat with owner")
    creator_user_id = fields.BigIntField(description="User ID who created the event")

    event_name = fields.CharField(max_length=200, description="Event name/title")
    description = fields.TextField(null=True, description="Event description")
    location = fields.CharField(max_length=500, null=True, description="Event location")

    event_datetime = fields.DatetimeField(description="When the event happens")
    end_datetime = fields.DatetimeField(null=True, description="When the event ends (optional)")
    timezone = fields.CharField(max_length=50, default="UTC")

    reminder_times = fields.JSONField(default=list, description="List of reminder times in minutes before event")
    sent_reminders = fields.JSONField(default=list, description="List of already sent reminder times")

    calendar_event_id = fields.CharField(max_length=200, null=True, description="CalDAV event ID")
    calendar_url = fields.CharField(max_length=500, null=True, description="CalDAV event URL")

    is_completed = fields.BooleanField(default=False, description="Whether event is completed")
    is_cancelled = fields.BooleanField(default=False, description="Whether event is cancelled")
    is_pinned = fields.BooleanField(default=True, description="Whether message is pinned in chat")

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "events"
        ordering = ["event_datetime"]

    def __str__(self) -> str:
        return f"Event({self.event_name} at {self.event_datetime})"

    @property
    def is_overdue(self) -> bool:
        now = datetime.utcnow()

        if self.event_datetime.tzinfo is not None and now.tzinfo is None:
            now = pytz.UTC.localize(now)
        elif self.event_datetime.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)

        return now > self.event_datetime and not self.is_completed

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.end_datetime:
            delta = self.end_datetime - self.event_datetime
            return int(delta.total_seconds() / 60)
        return None

    def get_pending_reminders(self) -> List[int]:
        return [time for time in self.reminder_times if time not in self.sent_reminders]

    def mark_reminder_sent(self, reminder_time: int) -> None:
        if reminder_time not in self.sent_reminders:
            self.sent_reminders.append(reminder_time)

    async def mark_completed(self) -> None:
        self.is_completed = True
        self.is_pinned = False
        await self.save(update_fields=["is_completed", "is_pinned", "updated_at"])

    async def mark_cancelled(self) -> None:
        self.is_cancelled = True
        self.is_pinned = False
        await self.save(update_fields=["is_cancelled", "is_pinned", "updated_at"])

from datetime import datetime, timezone
from tortoise import fields
from tortoise.models import Model


class AstroDocument(Model):
    id = fields.IntField(pk=True)

    content = fields.TextField(description="Document content text")

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "astro_documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        preview = self.content[:50] if self.content else ""
        return f"AstroDocument(id={self.id}, preview={preview}...)"

    @classmethod
    async def get_latest(cls):
        return await cls.all().order_by("-created_at").first()

    @classmethod
    async def delete_all(cls):
        await cls.all().delete()

    @classmethod
    async def is_outdated(cls, days: int = 7) -> bool:
        latest = await cls.get_latest()
        if not latest:
            return True

        now = datetime.now(timezone.utc)
        created_at = latest.created_at
        
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        age_days = (now - created_at).days
        return age_days >= days


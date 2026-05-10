import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class APIKey(models.Model):
    SOURCE_PORTAL = "portal"
    SOURCE_CLIPROXY = "cliproxy"
    SOURCE_CHOICES = [
        (SOURCE_PORTAL, "Portal 生成"),
        (SOURCE_CLIPROXY, "CLIProxy 绑定"),
    ]

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待审批"),
        (STATUS_ACTIVE, "启用"),
        (STATUS_REVOKED, "已禁用"),
        (STATUS_EXPIRED, "已过期"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True)
    token_prefix = models.CharField(max_length=24, db_index=True)
    token_masked = models.CharField(max_length=32, blank=True)
    token_plaintext = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_PORTAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def generate_token(cls) -> str:
        return f"labsk-{secrets.token_urlsafe(24).replace('-', 'A').replace('_', 'B')[:24]}"

    @classmethod
    def build_token_metadata(cls, raw_token: str) -> dict:
        return {
            "token_hash": cls.hash_token(raw_token),
            "token_prefix": raw_token[:12],
            "token_masked": f"{raw_token[:8]}...{raw_token[-4:]}",
        }

    @property
    def is_usable(self) -> bool:
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True


class APIKeyRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待审批"),
        (STATUS_APPROVED, "已批准"),
        (STATUS_REJECTED, "已拒绝"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_key_requests")
    name = models.CharField(max_length=100)
    reason = models.TextField()
    requested_models = models.CharField(max_length=255, blank=True)
    requested_quota = models.PositiveBigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.status})"

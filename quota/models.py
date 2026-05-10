from django.conf import settings
from django.db import models


class UserQuotaSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quota_snapshots")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    token_limit = models.PositiveBigIntegerField(default=0)
    token_used = models.PositiveBigIntegerField(default=0)
    cost_limit = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    cost_used = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "user__username"]
        unique_together = [("user", "year", "month")]

    def __str__(self):
        return f"{self.user.username} {self.year}-{self.month:02d}"

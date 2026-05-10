from django.conf import settings
from django.db import models


class Profile(models.Model):
    GROUP_MECH = "机械"
    GROUP_ALGO = "算法"
    GROUP_CONTROL = "电控"
    GROUP_MEDIA = "宣传"
    GROUP_CHOICES = [
        (GROUP_CONTROL, "电控"),
        (GROUP_ALGO, "算法"),
        (GROUP_MECH, "机械"),
        (GROUP_MEDIA, "宣传"),
    ]

    MEMBER_CORE = "正式队员"
    MEMBER_RESERVE = "梯队队员"
    MEMBER_TYPE_CHOICES = [
        (MEMBER_CORE, "正式队员"),
        (MEMBER_RESERVE, "梯队队员"),
    ]

    ROLE_USER = "user"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_USER, "普通用户"),
        (ROLE_ADMIN, "管理员"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    lab_group = models.CharField(max_length=100, blank=True, choices=GROUP_CHOICES)
    member_type = models.CharField(max_length=30, blank=True, choices=MEMBER_TYPE_CHOICES, default=MEMBER_CORE)
    grade = models.CharField(max_length=10, blank=True)
    is_dashboard_visible = models.BooleanField(default=True)
    monthly_token_quota = models.PositiveBigIntegerField(default=0)
    monthly_cost_quota = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        indexes = [
            models.Index(fields=["lab_group"]),
            models.Index(fields=["grade"]),
            models.Index(fields=["is_dashboard_visible"]),
        ]

    def __str__(self):
        return self.display_name or self.user.username

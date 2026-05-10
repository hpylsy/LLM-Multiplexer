from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import Profile


User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    full_name = (instance.get_full_name() or "").strip()
    default_display_name = full_name or instance.username
    if created:
        Profile.objects.create(
            user=instance,
            display_name=default_display_name,
            role=Profile.ROLE_ADMIN if instance.is_staff or instance.is_superuser else Profile.ROLE_USER,
        )
    else:
        profile, _ = Profile.objects.get_or_create(
            user=instance,
            defaults={
                "display_name": default_display_name,
                "role": Profile.ROLE_ADMIN if instance.is_staff or instance.is_superuser else Profile.ROLE_USER,
            },
        )

        # 避免每次用户保存时把管理员手工维护的显示名覆盖回 username/full_name
        if not (profile.display_name or "").strip():
            profile.display_name = default_display_name

        profile.save(update_fields=["display_name", "updated_at"])

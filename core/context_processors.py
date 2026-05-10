from django.conf import settings


def site_settings(request):
    return {
        "PUBLIC_DASHBOARD_ENABLED": settings.PUBLIC_DASHBOARD_ENABLED,
        "PUBLIC_DASHBOARD_MASK_USERNAMES": settings.PUBLIC_DASHBOARD_MASK_USERNAMES,
    }

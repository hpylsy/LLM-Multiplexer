from django.conf import settings


def site_settings(request):
    return {
        "PUBLIC_DASHBOARD_ENABLED": settings.PUBLIC_DASHBOARD_ENABLED,
        "PUBLIC_DASHBOARD_MASK_USERNAMES": settings.PUBLIC_DASHBOARD_MASK_USERNAMES,
        "SITE_TITLE": settings.SITE_TITLE,
        "SITE_SUBTITLE": settings.SITE_SUBTITLE,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "SITE_TEAM_NAME": settings.SITE_TEAM_NAME,
        "SITE_MOTTO": settings.SITE_MOTTO,
        "SITE_MOTTO_DESCRIPTION": settings.SITE_MOTTO_DESCRIPTION,
    }

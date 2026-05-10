from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://127.0.0.1,http://localhost").split(",") if origin.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "users",
    "api_keys",
    "usage",
    "dashboard",
    "quota",
]

AUTH_PROFILE_MODULE = "users.Profile"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lab_portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "lab_portal.wsgi.application"
ASGI_APPLICATION = "lab_portal.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "lab_portal"),
        "USER": os.getenv("POSTGRES_USER", "lab_portal"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "lab_portal_password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "zh-hans")
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PUBLIC_DASHBOARD_ENABLED = env_bool("PUBLIC_DASHBOARD_ENABLED", True)
PUBLIC_DASHBOARD_MASK_USERNAMES = env_bool("PUBLIC_DASHBOARD_MASK_USERNAMES", True)

CLIPROXY_BASE_URL = os.getenv("CLIPROXY_BASE_URL", "http://154.201.92.23")
CLIPROXY_MANAGEMENT_BASE_URL = os.getenv("CLIPROXY_MANAGEMENT_BASE_URL", "http://154.201.92.23:8317")
CLIPROXY_MANAGEMENT_KEY = os.getenv("CLIPROXY_MANAGEMENT_KEY", "")

# --- Branding (customizable via .env) ---
SITE_TITLE = os.getenv("SITE_TITLE", "AI中转站")
SITE_SUBTITLE = os.getenv("SITE_SUBTITLE", "AI Relay Console")
SITE_DESCRIPTION = os.getenv("SITE_DESCRIPTION", "面向团队成员统一提供大模型中转、调用统计与额度管理服务。")
SITE_TEAM_NAME = os.getenv("SITE_TEAM_NAME", "")
SITE_MOTTO = os.getenv("SITE_MOTTO", "")
SITE_MOTTO_DESCRIPTION = os.getenv("SITE_MOTTO_DESCRIPTION", "")

# --- Security settings (production) ---
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Only enable secure cookies when HTTPS is configured
    if "https" in CSRF_TRUSTED_ORIGINS[0] if CSRF_TRUSTED_ORIGINS else False:
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

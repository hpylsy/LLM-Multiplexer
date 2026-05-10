from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "admin":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("需要管理员权限")

    return _wrapped

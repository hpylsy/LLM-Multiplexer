from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from api_keys.models import APIKey
from core.utils import admin_required
from quota.models import UserQuotaSnapshot
from django.db.models import Sum

from users.forms import AdminProfileQuotaForm, AdminUserBoundKeyForm, AdminUserKeyOnlyForm, AdminUserPasswordForm, AdminUserWithCliproxyKeyForm, ProfileForm


@login_required
def profile_detail(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已更新")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    snapshots = UserQuotaSnapshot.objects.filter(user=request.user)[:6]
    return render(request, "users/profile.html", {"form": form, "snapshots": snapshots})


@admin_required
def admin_user_list(request):
    users = User.objects.select_related("profile").order_by("username")
    monthly_usage = {
        row["usage_logs__user"]: row["total_tokens"]
        for row in User.objects.filter(usage_logs__isnull=False)
        .values("usage_logs__user")
        .annotate(total_tokens=Sum("usage_logs__total_tokens"))
        .values("usage_logs__user", "total_tokens")
    }
    return render(request, "users/admin_user_list.html", {"users": users, "monthly_usage": monthly_usage})


@admin_required
def admin_user_edit(request, user_id):
    target_user = get_object_or_404(User.objects.select_related("profile"), pk=user_id)
    bound_key = target_user.api_keys.order_by("-created_at").first()
    if request.method == "POST":
        form = AdminProfileQuotaForm(request.POST, instance=target_user.profile, prefix="profile", user_instance=target_user)
        password_form = AdminUserPasswordForm(request.POST, prefix="password")
        key_form = AdminUserBoundKeyForm(request.POST, instance=bound_key, prefix="key") if bound_key else AdminUserKeyOnlyForm(request.POST, prefix="key")
        if "save_profile" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "用户信息已更新")
            return redirect("admin-user-list")
        if "save_key" in request.POST and key_form.is_valid() and bound_key:
            key = key_form.save(commit=False)
            metadata = APIKey.build_token_metadata(key_form.cleaned_data["token_plaintext"])
            key.token_hash = metadata["token_hash"]
            key.token_prefix = metadata["token_prefix"]
            key.token_masked = metadata["token_masked"]
            key.save()
            messages.success(request, "绑定密钥已更新")
            return redirect("admin-user-list")
        if "save_password" in request.POST and password_form.is_valid():
            target_user.set_password(password_form.cleaned_data["new_password"])
            target_user.save()
            messages.success(request, "用户密码已更新")
            return redirect("admin-user-list")
        if "delete_user" in request.POST:
            target_user.delete()
            messages.success(request, "用户账号已注销")
            return redirect("admin-user-list")
    else:
        form = AdminProfileQuotaForm(instance=target_user.profile, prefix="profile", user_instance=target_user)
        password_form = AdminUserPasswordForm(prefix="password")
        key_form = AdminUserBoundKeyForm(instance=bound_key, prefix="key") if bound_key else None
    return render(request, "users/admin_user_edit.html", {"target_user": target_user, "form": form, "password_form": password_form, "key_form": key_form, "bound_key": bound_key})


@admin_required
def admin_user_create(request):
    if request.method == "POST":
        form = AdminUserWithCliproxyKeyForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                )
                profile = user.profile
                profile.display_name = form.cleaned_data["display_name"]
                profile.lab_group = form.cleaned_data["lab_group"]
                profile.grade = form.cleaned_data["grade"]
                profile.member_type = form.cleaned_data["member_type"]
                profile.save()

                raw_token = form.cleaned_data["cliproxy_key_plaintext"]
                metadata = APIKey.build_token_metadata(raw_token)
                APIKey.objects.create(
                    user=user,
                    name="API 密钥",
                    token_hash=metadata["token_hash"],
                    token_prefix=metadata["token_prefix"],
                    token_masked=metadata["token_masked"],
                    token_plaintext=raw_token,
                    source=APIKey.SOURCE_CLIPROXY,
                    status=APIKey.STATUS_ACTIVE,
                    note=form.cleaned_data["member_type"],
                )

            messages.success(request, "用户和 CLIProxy Key 绑定已创建")
            return redirect("admin-user-list")
    else:
        form = AdminUserWithCliproxyKeyForm()
    return render(request, "users/admin_user_create.html", {"form": form})

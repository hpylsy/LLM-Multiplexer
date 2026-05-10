from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from api_keys.models import APIKey
from core.utils import admin_required
from quota.models import UserQuotaSnapshot
from django.db.models import Sum
from users.models import Profile

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

    # Filters
    group_filter = request.GET.get("group", "all")
    grade_filter = request.GET.get("grade", "all")
    status_filter = request.GET.get("status", "all")

    if group_filter != "all":
        users = users.filter(profile__lab_group=group_filter)
    if grade_filter != "all":
        users = users.filter(profile__grade=grade_filter)
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "disabled":
        users = users.filter(is_active=False)

    # Get filter options
    all_groups = sorted(set(
        Profile.objects.exclude(lab_group="").values_list("lab_group", flat=True).distinct()
    ))
    all_grades = sorted(set(
        Profile.objects.exclude(grade="").values_list("grade", flat=True).distinct()
    ))

    monthly_usage = {
        row["usage_logs__user"]: row["total_tokens"]
        for row in User.objects.filter(usage_logs__isnull=False)
        .values("usage_logs__user")
        .annotate(total_tokens=Sum("usage_logs__total_tokens"))
        .values("usage_logs__user", "total_tokens")
    }
    return render(request, "users/admin_user_list.html", {
        "users": users,
        "monthly_usage": monthly_usage,
        "group_filter": group_filter,
        "grade_filter": grade_filter,
        "status_filter": status_filter,
        "all_groups": all_groups,
        "all_grades": all_grades,
    })


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


@admin_required
def admin_user_toggle(request, user_id):
    """Toggle user active/disabled status."""
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active"])
        status_text = "启用" if target_user.is_active else "停用"
        messages.success(request, f"用户 {target_user.username} 已{status_text}")
    return redirect("admin-user-list")


@admin_required
def admin_user_delete(request, user_id):
    """Delete a user."""
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        username = target_user.username
        target_user.delete()
        messages.success(request, f"用户 {username} 已删除")
    return redirect("admin-user-list")


@admin_required
def admin_user_batch(request):
    """Batch operations on multiple users."""
    if request.method == "POST":
        action = request.POST.get("batch_action", "")
        user_ids = request.POST.getlist("user_ids")
        if not user_ids:
            messages.warning(request, "未选择任何用户")
            return redirect("admin-user-list")

        users_qs = User.objects.filter(id__in=user_ids, is_staff=False)
        count = users_qs.count()

        if action == "disable":
            users_qs.update(is_active=False)
            messages.success(request, f"已停用 {count} 个用户")
        elif action == "enable":
            users_qs.update(is_active=True)
            messages.success(request, f"已启用 {count} 个用户")
        elif action == "delete":
            users_qs.delete()
            messages.success(request, f"已删除 {count} 个用户")
        else:
            messages.warning(request, "未知操作")

    return redirect("admin-user-list")

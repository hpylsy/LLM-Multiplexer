from django import forms
from django.contrib.auth.models import User

from api_keys.models import APIKey
from users.models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "lab_group", "is_dashboard_visible"]


class AdminProfileQuotaForm(forms.ModelForm):
    username = forms.CharField(label="用户名", max_length=150)

    class Meta:
        model = Profile
        fields = ["display_name", "role", "lab_group", "grade", "member_type", "is_dashboard_visible"]

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop("user_instance", None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields["username"].initial = self.user_instance.username

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if self.user_instance and username != self.user_instance.username:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("该用户名已存在")
        return username

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user_instance:
            new_username = self.cleaned_data["username"]
            if new_username != self.user_instance.username:
                self.user_instance.username = new_username
                self.user_instance.save(update_fields=["username"])
        return profile


class AdminUserWithCliproxyKeyForm(forms.Form):
    username = forms.CharField(label="用户名", max_length=150)
    password = forms.CharField(label="初始密码", widget=forms.PasswordInput)
    display_name = forms.CharField(label="显示名", max_length=150)
    lab_group = forms.ChoiceField(label="实验室分组", choices=Profile.GROUP_CHOICES)
    grade = forms.RegexField(label="年级", regex=r"^20\d{2}$", help_text="请输入 20xx 格式，例如 2024")
    member_type = forms.ChoiceField(label="队员身份", choices=Profile.MEMBER_TYPE_CHOICES)
    cliproxy_key_plaintext = forms.CharField(label="CLIProxy API Key 明文", widget=forms.TextInput)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("该用户名已存在")
        return username

    def clean_cliproxy_key_plaintext(self):
        raw_token = self.cleaned_data["cliproxy_key_plaintext"].strip()
        metadata = APIKey.build_token_metadata(raw_token)
        if APIKey.objects.filter(token_hash=metadata["token_hash"]).exists():
            raise forms.ValidationError("该 CLIProxy API Key 已经绑定过")
        return raw_token


class AdminUserBoundKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ["name", "token_plaintext", "status", "note"]


class AdminUserKeyOnlyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ["token_plaintext", "status", "note"]


class AdminUserPasswordForm(forms.Form):
    new_password = forms.CharField(label="新密码", widget=forms.PasswordInput)

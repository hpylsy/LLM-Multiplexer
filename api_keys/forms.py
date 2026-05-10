from django import forms

from api_keys.models import APIKey, APIKeyRequest


class APIKeyRequestForm(forms.ModelForm):
    class Meta:
        model = APIKeyRequest
        fields = ["name", "reason", "requested_models", "requested_quota"]


class APIKeyAdminForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ["name", "status", "expires_at", "note"]


class APIKeyReviewForm(forms.ModelForm):
    class Meta:
        model = APIKeyRequest
        fields = ["status", "admin_comment"]

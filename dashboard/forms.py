from django import forms

from dashboard.models import ModelPricing


class ModelPricingForm(forms.ModelForm):
    class Meta:
        model = ModelPricing
        fields = ["model_name", "prompt_price_per_million", "completion_price_per_million", "cached_price_per_million"]


from django import forms

from dashboard.models import ModelPricing
from usage.models import UsageLog


class ModelPricingForm(forms.ModelForm):
    class Meta:
        model = ModelPricing
        fields = ["model_name", "prompt_price_per_million", "completion_price_per_million", "cached_price_per_million"]
        widgets = {
            "prompt_price_per_million": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": "0.00"}),
            "completion_price_per_million": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": "0.00"}),
            "cached_price_per_million": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get models that have usage but no pricing yet
        priced_models = set(ModelPricing.objects.values_list("model_name", flat=True))
        used_models = sorted(set(
            UsageLog.objects.exclude(model_name="")
            .values_list("model_name", flat=True).distinct()
        ))
        unpriced = [m for m in used_models if m not in priced_models]

        # Build choices: unpriced first, then already priced (for editing)
        choices = [("", "— 选择模型 —")]
        if unpriced:
            choices.append(("未定价模型", [(m, f"⚠️ {m}") for m in unpriced]))
        if priced_models:
            choices.append(("已定价模型", [(m, f"✓ {m}") for m in sorted(priced_models)]))

        self.fields["model_name"] = forms.ChoiceField(
            choices=choices,
            label="模型名称",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

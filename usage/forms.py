from django import forms


class UsageLogUploadForm(forms.Form):
    source_file = forms.FileField(label="上传 CSV 或 JSONL")

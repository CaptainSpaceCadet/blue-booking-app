from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import UserProfile
from apps.campaigns.services import has_reached_campaign_limit


class CreateCampaignForm(forms.Form):
    title = forms.CharField(max_length=100, required=True)
    description = forms.CharField(max_length=500, required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.user_profile = kwargs.pop("user_profile", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.user_profile and has_reached_campaign_limit(self.user_profile):
            raise ValidationError(
                "You have reached the maximum number of campaigns you are allowed to join."
            )

        return cleaned_data

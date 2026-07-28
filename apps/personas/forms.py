from django import forms

from apps.personas.services import has_reached_persona_limit


class CreatePersonaForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    description = forms.CharField(
        max_length=500, required=False, widget=forms.HiddenInput
    )

    def __init__(self, *args, **kwargs):
        self.campaign_membership = kwargs.pop("campaign_membership", None)
        super().__init__(*args, **kwargs)

    # NOTE: This will not sanitize the Markdown content for dangerous HTML that is instead done when the content is displayed.
    def clean(self):
        cleaned_data = super().clean()

        if self.campaign_membership and has_reached_persona_limit(
            self.campaign_membership
        ):
            raise forms.ValidationError(
                "You have created the maximum number of personas you are allowed to create."
            )

        return cleaned_data


class EditPersonaForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    description = forms.CharField(
        max_length=500, required=False, widget=forms.HiddenInput
    )

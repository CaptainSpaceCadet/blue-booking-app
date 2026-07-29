from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render

from apps.accounts.models import UserProfile

class CustomSignupForm(forms.Form):
    display_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Display Name"}),
    )

    def signup(self, request, user):
        """Called after user is created but before it is saved. It functions to save additional fields."""
        user.save()

        profile = UserProfile.objects.create(user=user)
        profile.display_name = self.cleaned_data["display_name"]
        profile.save()

class ChangeDisplayNameForm(forms.Form):
    display_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Display Name"}),
    )


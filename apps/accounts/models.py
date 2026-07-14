from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    display_name = models.CharField(blank=True, null=False, max_length=100)

    campaigns = models.ManyToManyField(
        "campaigns.Campaign",
        through="campaigns.CampaignMembership",
        related_name="members",
    )

    def __str__(self) -> str:
        return f"{self.display_name}({self.user.username})'s profile"

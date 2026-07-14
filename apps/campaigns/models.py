from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Campaign(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    users = models.ManyToManyField("accounts.UserProfile", through="CampaignMembership")

    def __str__(self) -> str:
        return self.title


class CampaignMembership(models.Model):
    class Meta:
        unique_together = ["user", "campaign"]

    class CampaignRoles(models.TextChoices):
        GM = "GM", "Game Master"
        PLAYER = "PLAYER", "Player"

    role = models.CharField(max_length=15, choices=CampaignRoles.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    def is_last_member(self) -> bool:
        """Check if this membership is the only one in the campaign."""
        campaign = self.campaign
        return campaign.campaignmembership_set.count() == 1

    def is_last_gm(self) -> bool:
        """Check if this membership is the only GM in the campaign."""
        if self.role != "GM":
            return False
        return (
            self.campaign.campaignmembership_set.filter(
                role=self.CampaignRoles.GM
            ).count()
            == 1
        )

    def delete(self, *args, **kwargs) -> None:
        """
        Delete the campaign membership.

        A campaign must have at least one GM. Therefore, ValidationError is raised if a membership to-be-deleted is
        the sole GM and there is still other members of the campaign.

        :param args: Used in delete super() call
        :param kwargs: Used in delete super() call
        :raises ValidationError: If this membership is the last but not the last member
        """

        is_last_member = self.is_last_member()
        is_last_gm = self.is_last_gm()
        if is_last_gm and not is_last_member:
            raise ValidationError("Cannot delete the last GM. Assign another GM first.")

        campaign = self.campaign
        super().delete(*args, **kwargs)

        if is_last_member:
            campaign.delete()

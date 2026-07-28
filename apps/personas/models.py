from django.db import models


class Persona(models.Model):
    class PersonaType(models.TextChoices):
        PLAYER = "PLAYER", "Player"
        GM = "GM", "Game Master"
        CHARACTER = "CHARACTER", "Character"
        NPC = "NPC", "Non-Player Character"

    class PersonaStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETIRED = "RETIRED", "Retired"

    name = models.CharField(max_length=100, blank=False)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    type = models.CharField(max_length=15, choices=PersonaType.choices)
    status = models.CharField(max_length=15, choices=PersonaStatus.choices)

    # I could keep a reference to the original creator.
    # However, for the moment that's too much of a pain.

    member = models.ForeignKey(
        "campaigns.CampaignMembership",
        on_delete=models.CASCADE,
        related_name="personas",
    )

    def __str__(self) -> str:
        return self.name

    def is_member_type(self) -> bool:
        return self.type == self.PersonaType.PLAYER or self.type == self.PersonaType.GM

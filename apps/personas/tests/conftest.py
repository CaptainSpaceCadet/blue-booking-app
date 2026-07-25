# tests/personas/fixtures.py
import pytest
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from apps.campaigns.models import Campaign, CampaignMembership
from apps.personas.models import Persona


@pytest.fixture
def user_profile(db):
    user = User.objects.create_user(username="testuser", password="testpass")
    return UserProfile.objects.create(user=user, display_name="Test User")


@pytest.fixture
def user_profile2(db):
    user = User.objects.create_user(username="testuser2", password="testpass2")
    return UserProfile.objects.create(user=user, display_name="Test User 2")


@pytest.fixture
def user_profile3(db):
    user = User.objects.create_user(username="testuser3", password="testpass3")
    return UserProfile.objects.create(user=user, display_name="Test User 3")


@pytest.fixture
def campaign(db, user_profile):
    return Campaign.objects.create(
        title="Test Campaign", description="Test Description"
    )


@pytest.fixture
def gm_membership(db, campaign, user_profile):
    return CampaignMembership.objects.create(
        campaign=campaign, user=user_profile, role=CampaignMembership.CampaignRoles.GM
    )


@pytest.fixture
def player_membership(db, campaign, user_profile2):
    return CampaignMembership.objects.create(
        campaign=campaign,
        user=user_profile2,
        role=CampaignMembership.CampaignRoles.PLAYER,
    )


@pytest.fixture
def player_membership2(db, campaign, user_profile3):
    return CampaignMembership.objects.create(
        campaign=campaign,
        user=user_profile3,
        role=CampaignMembership.CampaignRoles.PLAYER,
    )


@pytest.fixture
def gm_persona(db, gm_membership):
    return Persona.objects.create(
        member=gm_membership,
        name="GM Persona",
        type=Persona.PersonaType.GM,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def gm_membership2(db, campaign, user_profile3):
    return CampaignMembership.objects.create(
        campaign=campaign, user=user_profile3, role=CampaignMembership.CampaignRoles.GM
    )


@pytest.fixture
def gm_persona2(db, gm_membership2):
    return Persona.objects.create(
        member=gm_membership2,
        name="GM Persona 2",
        type=Persona.PersonaType.GM,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def player_persona(db, player_membership):
    return Persona.objects.create(
        member=player_membership,
        name="Player Persona",
        type=Persona.PersonaType.PLAYER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def player_character_persona(db, player_membership):
    return Persona.objects.create(
        member=player_membership,
        name="Character Persona",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def gm_character_persona(db, gm_membership):
    return Persona.objects.create(
        member=gm_membership,
        name="Character Persona Belonging to GM",
        status=Persona.PersonaStatus.ACTIVE,
        type=Persona.PersonaType.CHARACTER,
    )


@pytest.fixture
def npc_persona(db, gm_membership):
    return Persona.objects.create(
        member=gm_membership,
        name="NPC Persona",
        type=Persona.PersonaType.NPC,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def retired_persona(db, gm_membership):
    return Persona.objects.create(
        member=gm_membership,
        name="Retired Persona",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.RETIRED,
    )


@pytest.fixture
def campaign_with_members(db, campaign, gm_membership, player_membership):
    return campaign

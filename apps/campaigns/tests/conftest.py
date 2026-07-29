import pytest
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.campaigns.models import Campaign, CampaignMembership
from apps.personas.models import Persona
from blue_booking_app.settings import CAMPAIGN_MEMBER_LIMIT, USER_CAMPAIGN_LIMIT

# Tests for campaigns
# user 4 x
# player_user_profile 2 (didn't do)
# gm_user_profile 2 (didn't do)
# campaign 1 x
# full campaign x
# empty campaign x
# user at campaign limit

# Tests for personas in campaigns
# player_user_profile 1
# - player persona
# player_userprofile 2
# - player persona
# - character persona
# - character persona
# gm_user_profile 1
# - gm persona
# gm_user_profile 2
# - gm persona
# - character persona
# - npc persona
# gm_user_profile 3
# - gm persona
# - retired persona


# region Users
@pytest.fixture
def user_profile1(db):
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
def user_profile4(db):
    user = User.objects.create_user(username="testuser4", password="testpass4")
    return UserProfile.objects.create(user=user, display_name="Test User 4")


@pytest.fixture
def user_profile_at_limit(db) -> UserProfile:
    limit_user = User.objects.create_user(username="limituser", password="limit")
    limit_profile = UserProfile.objects.create(
        user=limit_user, display_name="Limit User"
    )

    # Create gm for campaigns
    gm_user = User.objects.create_user(username="gmuser", password="gm")
    gm_profile = UserProfile.objects.create(user=gm_user, display_name="GM User")

    # Create campaigns with gm up to the limit
    for i in range(USER_CAMPAIGN_LIMIT):
        # Create campaign
        campaign = Campaign.objects.create(
            title=f"Campaign {i}", description=f"Test campaign {i}"
        )
        # Create gm membership
        gm_membership = CampaignMembership.objects.create(
            user=gm_profile, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
        )
        # Create gm persona
        Persona.objects.create(
            member=gm_membership,
            name=f"GM {i} Persona",
            type=Persona.PersonaType.GM,
            status=Persona.PersonaStatus.ACTIVE,
        )
        # Create player membership
        limit_member = CampaignMembership.objects.create(
            user=limit_profile,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        )
        # Create player persona
        Persona.objects.create(
            member=limit_member,
            name=f"Player {i} Persona",
            type=Persona.PersonaType.PLAYER,
            status=Persona.PersonaStatus.ACTIVE,
        )
    return limit_profile


# endregion


# region Campaigns
@pytest.fixture
def campaign(db):
    return Campaign.objects.create(
        title="Test Campaign", description="Test Description"
    )


@pytest.fixture
def full_campaign(db, user_profile1):
    campaign = Campaign.objects.create(
        title="Test Campaign", description="Test Description"
    )

    # Create initial gm membership
    gm_membership = CampaignMembership.objects.create(
        user=user_profile1, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
    )
    # Create initial gm persona
    Persona.objects.create(
        member=gm_membership,
        name="Test GM Persona",
        type=Persona.PersonaType.GM,
        status=Persona.PersonaStatus.ACTIVE,
    )

    # Create player memberships
    for i in range(CAMPAIGN_MEMBER_LIMIT - 1):
        # Create user
        user = User.objects.create_user(username=f"player{i}", password="testpass")
        user_profile = UserProfile.objects.create(user=user, display_name=f"Player {i}")
        # Create player membership
        user_membership = CampaignMembership.objects.create(
            user=user_profile,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        )
        # Create persona
        Persona.objects.create(
            member=user_membership,
            name=f"Player {i} Persona",
            type=Persona.PersonaType.PLAYER,
            status=Persona.PersonaStatus.ACTIVE,
        )
    return campaign


# endregion


# region Memberships
@pytest.fixture
def gm_membership1(db, campaign, user_profile1):
    return CampaignMembership.objects.create(
        campaign=campaign, user=user_profile1, role=CampaignMembership.CampaignRoles.GM
    )


@pytest.fixture
def gm_membership2(db, campaign, user_profile2):
    return CampaignMembership.objects.create(
        campaign=campaign, user=user_profile2, role=CampaignMembership.CampaignRoles.GM
    )


@pytest.fixture
def player_membership1(db, campaign, user_profile3):
    return CampaignMembership.objects.create(
        campaign=campaign,
        user=user_profile3,
        role=CampaignMembership.CampaignRoles.PLAYER,
    )


@pytest.fixture
def player_membership2(db, campaign, user_profile4):
    return CampaignMembership.objects.create(
        campaign=campaign,
        user=user_profile4,
        role=CampaignMembership.CampaignRoles.PLAYER,
    )


# endregion


# region Personas
@pytest.fixture
def gm_persona1(db, gm_membership1):
    return Persona.objects.create(
        member=gm_membership1,
        name="Test GM Persona 1",
        type=Persona.PersonaType.GM,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def character_persona1(db, gm_membership1):
    return Persona.objects.create(
        member=gm_membership1,
        name="Test Character Persona 1",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def npc_persona1(db, gm_membership1):
    return Persona.objects.create(
        member=gm_membership1,
        name="Test NPC Persona 1",
        type=Persona.PersonaType.NPC,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def retired_persona11(db, gm_membership1):
    return Persona.objects.create(
        member=gm_membership1,
        name="Test Retired Persona 1.1",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.RETIRED,
    )


@pytest.fixture
def retired_persona12(db, gm_membership1):
    return Persona.objects.create(
        member=gm_membership1,
        name="Test Retired Persona 1.2",
        type=Persona.PersonaType.NPC,
        status=Persona.PersonaStatus.RETIRED,
    )


@pytest.fixture
def gm_persona2(db, gm_membership2):
    return Persona.objects.create(
        member=gm_membership2,
        name="Test GM Persona 2",
        type=Persona.PersonaType.GM,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def character_persona2(db, gm_membership2):
    return Persona.objects.create(
        member=gm_membership2,
        name="Test Character Persona 2",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def npc_persona2(db, gm_membership2):
    return Persona.objects.create(
        member=gm_membership2,
        name="Test NPC Persona 2",
        type=Persona.PersonaType.NPC,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def player_persona1(db, player_membership1):
    return Persona.objects.create(
        member=player_membership1,
        name="Test Player Persona",
        type=Persona.PersonaType.PLAYER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def character_persona3(db, player_membership1):
    return Persona.objects.create(
        member=player_membership1,
        name="Test Character Persona 3",
        type=Persona.PersonaType.CHARACTER,
        status=Persona.PersonaStatus.ACTIVE,
    )


@pytest.fixture
def player_persona2(db, player_membership2):
    return Persona.objects.create(
        member=player_membership2,
        name="Test Player Persona 2",
        type=Persona.PersonaType.PLAYER,
        status=Persona.PersonaStatus.ACTIVE,
    )


# endregion

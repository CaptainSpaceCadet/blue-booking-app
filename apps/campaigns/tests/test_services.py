"""
Tests for campaign service layer.
"""

import pytest
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from apps.campaigns import services
from apps.campaigns.exceptions import (
    CampaignTitleIsInvalidError,
    UserCampaignMembershipLimitReachedError,
    CampaignDescriptionIsInvalidError,
    MemberNotGMError,
    MemberNotSoleGMError,
    UserAlreadyMemberError,
    CampaignMembershipFullError,
    UserNotMemberError,
    LastGMCannotLeaveError,
    MemberAlreadyGMError,
    MemberAlreadyPlayerError,
)
from apps.campaigns.models import CampaignMembership, Campaign
from apps.campaigns.tests.conftest import player_membership1
from apps.personas.models import Persona
from apps.personas.tests.conftest import gm_membership, gm_persona

# region Helper Function Tests


class TestHasReachedCampaignLimit:
    """Tests for has_reached_campaign_limit function."""

    def test_user_below_limit(self, user_profile1):
        """User with no campaigns should not have reached the limit."""
        assert services.has_reached_campaign_limit(user_profile1) is False

    def test_user_at_limit(self, user_profile_at_limit):
        """User at limit should return True."""
        assert services.has_reached_campaign_limit(user_profile_at_limit) is True

    def test_user_above_limit(self, user_profile_at_limit, campaign):
        """User above limit should return True."""

        # Have user join extra campaign
        CampaignMembership.objects.create(
            user=user_profile_at_limit,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        )
        assert services.has_reached_campaign_limit(user_profile_at_limit) is True


class TestIsCampaignMembershipFull:
    """Tests for is_campaign_membership_full function."""

    def test_campaign_empty(self, campaign):
        """Campaign with no members should not be full."""
        assert services.is_campaign_membership_full(campaign) is False

    def test_campaign_at_limit(self, full_campaign):
        """Campaign at limit should return True."""
        assert services.is_campaign_membership_full(full_campaign) is True


# endregion

# region Core Service Tests


class TestCreateCampaign:
    """Tests for create_campaign function."""

    @pytest.mark.success
    class TestSuccess:
        def test_create_campaign(self, user_profile1):
            """Successfully create a campaign with a GM."""
            campaign = services.create_campaign(
                creator=user_profile1,
                title="My Campaign",
                description="A great adventure",
            )

            # Assert campaign properties
            assert campaign.title == "My Campaign"
            assert campaign.description == "A great adventure"
            assert campaign.id is not None

            # Assert GM membership
            gm_membership = CampaignMembership.objects.get(
                user=user_profile1, campaign=campaign
            )
            assert gm_membership.role == CampaignMembership.CampaignRoles.GM

            # Assert gm member persona
            gm_member_persona = Persona.objects.get(
                member=gm_membership, type=Persona.PersonaType.GM
            )
            assert gm_member_persona.name == f"{user_profile1.display_name}"
            assert gm_member_persona.status == Persona.PersonaStatus.ACTIVE

    @pytest.mark.failure
    class TestFailure:
        def test_create_campaign_user_at_limit(self, user_profile_at_limit):
            """Raise error when a user has reached the campaign limit tries to create a campaign."""
            with pytest.raises(UserCampaignMembershipLimitReachedError):
                services.create_campaign(
                    creator=user_profile_at_limit,
                    title="My Campaign",
                    description="A great adventure",
                )

        def test_create_campaign_title_too_long(self, user_profile1):
            """Raise error when the title is too long."""
            with pytest.raises(CampaignTitleIsInvalidError) as exc_info:
                services.create_campaign(
                    creator=user_profile1,
                    title="A" * 101,
                    description="A great adventure",
                )

            assert "Title must be less than 100 characters" in str(exc_info.value)

        def test_create_campaign_description_too_long(self, user_profile1):
            """Raise error when the description is too long."""
            with pytest.raises(CampaignDescriptionIsInvalidError) as exc_info:
                services.create_campaign(
                    creator=user_profile1, title="My Campaign", description="A" * 501
                )

            assert "Description must be less than 500 characters" in str(exc_info.value)


class TestEditCampaign:
    """Tests for the edit_campaign function."""

    @pytest.mark.success
    class TestSuccess:
        def test_edit_campaign(self, campaign, user_profile1, gm_membership1):
            """Successfully edit a campaign."""
            campaign = services.edit_campaign(
                user_profile1, campaign, "My Edited Campaign", "An edited adventure"
            )

            # Assert campaign properties
            assert campaign.title == "My Edited Campaign"
            assert campaign.description == "An edited adventure"
            assert campaign.id is not None

    @pytest.mark.failure
    class TestFailure:
        def test_editor_not_gm(
            self, campaign, user_profile2, user_profile3, player_membership1
        ):
            """Raise error when the editor is not a GM."""
            # Test when editor is not a member of the campaign
            with pytest.raises(MemberNotGMError):
                services.edit_campaign(
                    user_profile2, campaign, "My Edited Campaign", "An edited adventure"
                )

            # Test when editor is a player
            with pytest.raises(MemberNotGMError):
                services.edit_campaign(
                    user_profile3, campaign, "My Edited Campaign", "An edited adventure"
                )

        def test_create_campaign_title_too_long(
            self, campaign, user_profile1, gm_membership1
        ):
            """Raise error when the title is too long."""
            with pytest.raises(CampaignTitleIsInvalidError) as exc_info:
                services.edit_campaign(
                    editor=user_profile1,
                    campaign=campaign,
                    title="A" * 101,
                    description="A great adventure",
                )

            assert "Title must be less than 100 characters" in str(exc_info.value)

        def test_create_campaign_description_too_long(
            self, campaign, user_profile1, gm_membership1
        ):
            """Raise error when the description is too long."""
            with pytest.raises(CampaignDescriptionIsInvalidError) as exc_info:
                services.edit_campaign(
                    editor=user_profile1,
                    campaign=campaign,
                    title="My Campaign",
                    description="A" * 501,
                )

            assert "Description must be less than 500 characters" in str(exc_info.value)


class TestDeleteCampaign:
    """Tests for the delete_campaign function."""

    @pytest.mark.success
    class TestSuccess:
        def test_delete_campaign(self, campaign, user_profile1, gm_membership1):
            """Successfully delete a campaign with no other players in the campaign."""
            campaign_id = campaign.id
            gm_membership_id = gm_membership1.id
            services.delete_campaign(user_profile1, campaign)

            # Assert campaign is deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()

            # Assert campaign membership is deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()
            assert not CampaignMembership.objects.filter(id=gm_membership_id).exists()

            # Assert personas are deleted
            assert not Persona.objects.filter(member__campaign_id=campaign_id).exists()
            assert not Persona.objects.filter(member_id=gm_membership_id).exists()

        def test_delete_campaign_with_players(
            self,
            campaign,
            user_profile1,
            user_profile3,
            user_profile4,
            gm_membership1,
            player_membership1,
            player_membership2,
        ):
            """Successfully delete a campaign when there are players in the campaign."""
            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            player_membership1_id = player_membership1.id
            player_membership2_id = player_membership2.id
            services.delete_campaign(user_profile1, campaign)

            # Assert campaign is deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()

            # Assert all the campaign memberships are deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()
            assert not CampaignMembership.objects.filter(
                id=player_membership1_id
            ).exists()
            assert not CampaignMembership.objects.filter(
                id=player_membership2_id
            ).exists()

            # Assert personas are deleted
            assert not Persona.objects.filter(member__campaign_id=campaign_id).exists()
            assert not Persona.objects.filter(member_id=gm_membership1_id).exists()
            assert not Persona.objects.filter(member_id=player_membership1_id).exists()
            assert not Persona.objects.filter(member_id=player_membership2_id).exists()

    @pytest.mark.failure
    class TestFailure:
        def test_delete_campaign_not_sole_gm(
            self,
            campaign,
            user_profile1,
            user_profile2,
            user_profile3,
            user_profile4,
            gm_membership1,
            gm_membership2,
            player_membership1,
        ):
            """Raise error when the user is not the sole GM."""

            # Test when deleter is not a member of the campaign
            with pytest.raises(MemberNotSoleGMError):
                services.delete_campaign(user_profile4, campaign)

            # Test when deleter is a player
            with pytest.raises(MemberNotSoleGMError):
                services.delete_campaign(user_profile3, campaign)

            # Test when deleter is a GM but not the sole GM
            with pytest.raises(MemberNotSoleGMError):
                services.delete_campaign(user_profile2, campaign)


class TestJoinCampaign:
    """Tests for the join_campaign function."""

    @pytest.mark.success
    class TestSuccess:
        def test_join_campaign(
            self, campaign, user_profile1, gm_membership1, user_profile2
        ):
            """Successfully join a campaign as a PLAYER."""
            membership = services.join_campaign(user=user_profile2, campaign=campaign)

            # Assert campaign membership exists
            assert CampaignMembership.objects.filter(
                user=user_profile2, campaign=campaign
            ).exists()

            # Assert membership properties
            assert membership.user == user_profile2
            assert membership.campaign == campaign
            assert membership.role == CampaignMembership.CampaignRoles.PLAYER
            assert membership.id is not None

            # Assert member persona exists
            assert Persona.objects.filter(member=membership).exists()

            # Assert persona properties
            persona = Persona.objects.get(member=membership)
            assert persona.name == f"{user_profile2.display_name}"
            assert persona.status == Persona.PersonaStatus.ACTIVE
            assert persona.type == Persona.PersonaType.PLAYER
            assert persona.id is not None

    @pytest.mark.failure
    class TestFailure:
        def test_join_campaign_already_member(
            self,
            campaign,
            user_profile1,
            gm_membership1,
            user_profile3,
            player_membership1,
        ):
            """Raise error when a user tries to join a campaign it is already a member of."""

            # When a player tries to join a campaign they are already a member of
            with pytest.raises(UserAlreadyMemberError):
                services.join_campaign(user=user_profile3, campaign=campaign)

            # When a GM tries to join a campaign, they are already a member of
            with pytest.raises(UserAlreadyMemberError):
                services.join_campaign(user=player_membership1.user, campaign=campaign)

        def test_join_campaign_full(
            self, full_campaign, user_profile1, gm_membership1, user_profile2
        ):
            """Raise error when a user tries to join a campaign when it is already full."""
            with pytest.raises(CampaignMembershipFullError):
                services.join_campaign(user=user_profile2, campaign=full_campaign)

        def test_join_campaign_user_at_limit(
            self, campaign, user_profile1, gm_membership1, user_profile_at_limit
        ):
            """Raise error when a user that has reached the campaign limit tries to join a campaign."""
            with pytest.raises(UserCampaignMembershipLimitReachedError):
                services.join_campaign(user=user_profile_at_limit, campaign=campaign)


class TestLeaveCampaign:
    """Tests for the leave_campaign function."""

    @pytest.mark.success
    class TestSuccess:
        def test_leave_campaign_sole_gm_without_players(
            self, campaign, user_profile1, gm_membership1, gm_persona1
        ):
            """Successfully leave a campaign when the last GM without players."""
            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            gm_persona1_id = gm_persona1.id

            services.leave_campaign(member=user_profile1, campaign=campaign)

            # Assert the campaign memberships are deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()

            # Assert personas are deleted
            assert not Persona.objects.filter(member__campaign_id=campaign_id).exists()
            assert not Persona.objects.filter(member_id=gm_membership1_id).exists()
            assert not Persona.objects.filter(id=gm_persona1_id).exists()

            # Assert campaign should be deleted
            assert not Campaign.objects.filter(id=campaign_id).exists()

        def test_leave_campaign_sole_gm_without_players_with_personas(
            self,
            campaign,
            user_profile1,
            gm_membership1,
            gm_persona1,
            npc_persona1,
            character_persona1,
            retired_persona11,
            retired_persona12,
        ):
            """Successfully leave a campaign when the last GM without players. In addition, the last GM has NPC, Character, and Retired personas."""
            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id

            # All persona ids
            gm_persona1_id = gm_persona1.id
            npc_persona1_id = npc_persona1.id
            character_persona1_id = character_persona1.id
            retired_persona11_id = retired_persona11.id
            retired_persona12_id = retired_persona12.id

            services.leave_campaign(member=user_profile1, campaign=campaign)

            # Assert the campaign memberships are deleted
            assert not CampaignMembership.objects.filter(
                campaign_id=campaign_id
            ).exists()
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()

            # Assert personas are deleted
            assert not Persona.objects.filter(member__campaign_id=campaign_id).exists()
            assert not Persona.objects.filter(member_id=gm_membership1_id).exists()
            assert not Persona.objects.filter(id=gm_persona1_id).exists()
            assert not Persona.objects.filter(id=npc_persona1_id).exists()
            assert not Persona.objects.filter(id=character_persona1_id).exists()
            assert not Persona.objects.filter(id=retired_persona11_id).exists()
            assert not Persona.objects.filter(id=retired_persona12_id).exists()

            # Assert campaign should be deleted
            assert not Campaign.objects.filter(id=campaign_id).exists()

        def test_leave_campaign_non_sole_gm_entrustee_not_specified(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
        ):
            """Successfully leave a campaign when not the sole GM and the entrustee that will take care of the leaver's personas is not specified."""
            # TODO: Maybe I should test this with 3 GMs...

            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id

            # Leave the campaign without specifying the entrustee
            services.leave_campaign(member=user_profile1, campaign=campaign)

            # Assert campaign has not been deleted
            assert Campaign.objects.filter(id=campaign_id).exists()

            # Assert the leaving gm's campaign membership is deleted
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()

            # Refresh the personas
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()

            # Assert the leaving gm's personas have been entrusted to the second gm
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership2_id
            assert gm_persona1.type == Persona.PersonaType.GM
            assert gm_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the second gm's personas remain
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_leave_campaign_non_sole_gm_extra_personas(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
            npc_persona1,
            npc_persona2,
            character_persona1,
            character_persona2,
        ):
            """Successfully leave a campaign when not the sole GM and the entrustee that will take care of the leaver's personas is specified."""

            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            npc_persona1_id = npc_persona1.id
            npc_persona2_id = npc_persona2.id
            character_persona1_id = character_persona1.id
            character_persona2_id = character_persona2.id

            # Leave the campaign without specifying the entrustee
            services.leave_campaign(
                member=user_profile1, entrustee=user_profile2, campaign=campaign
            )

            # Assert campaign has not been deleted
            assert Campaign.objects.filter(id=campaign_id).exists()

            # Assert the leaving gm's campaign membership is deleted
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()

            # Refresh the personas
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            npc_persona1.refresh_from_db()
            npc_persona2.refresh_from_db()
            character_persona1.refresh_from_db()
            character_persona2.refresh_from_db()

            # Assert the leaving gm's personas have been entrusted to the second gm
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership2_id
            assert gm_persona1.type == Persona.PersonaType.GM
            assert gm_persona1.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=npc_persona1_id).exists()
            assert npc_persona1.member.id == gm_membership2_id
            assert npc_persona1.type == Persona.PersonaType.NPC
            assert npc_persona1.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=character_persona1_id).exists()
            assert character_persona1.member.id == gm_membership2_id
            assert character_persona1.type == Persona.PersonaType.CHARACTER
            assert character_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the second gm's personas remain
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE
            assert Persona.objects.filter(id=npc_persona2_id).exists()
            assert npc_persona2.member.id == gm_membership2_id
            assert npc_persona2.type == Persona.PersonaType.NPC
            assert npc_persona2.status == Persona.PersonaStatus.ACTIVE
            assert Persona.objects.filter(id=character_persona2_id).exists()
            assert character_persona2.member.id == gm_membership2_id
            assert character_persona2.type == Persona.PersonaType.CHARACTER
            assert character_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_leave_campaign_non_sole_gm_entrusted_personas(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
            retired_persona11,
            retired_persona12,
        ):
            """Successfully leave a campaign when not the sole GM and the entrustee that will take care of the leaver's personas is specified. Additionally, the demoting gm has personas that have been entrusted to it."""

            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            retired_persona11_id = retired_persona11.id
            retired_persona12_id = retired_persona12.id

            # Leave the campaign without specifying the entrustee
            services.leave_campaign(
                member=user_profile1, entrustee=user_profile2, campaign=campaign
            )

            # Assert campaign has not been deleted
            assert Campaign.objects.filter(id=campaign_id).exists()

            # Assert the leaving gm's campaign membership is deleted
            assert not CampaignMembership.objects.filter(id=gm_membership1_id).exists()

            # Refresh the personas
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            retired_persona11.refresh_from_db()
            retired_persona12.refresh_from_db()

            # Assert the leaving gm's personas have been entrusted to the second gm
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership2_id
            assert gm_persona1.type == Persona.PersonaType.GM
            assert gm_persona1.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=retired_persona11_id).exists()
            assert retired_persona11.member.id == gm_membership2_id
            assert retired_persona11.type == Persona.PersonaType.CHARACTER
            assert retired_persona11.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=retired_persona12_id).exists()
            assert retired_persona12.member.id == gm_membership2_id
            assert retired_persona12.type == Persona.PersonaType.NPC
            assert retired_persona12.status == Persona.PersonaStatus.RETIRED

            # Assert the second gm's personas remain
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_leave_campaign_player_entrustee_not_specified_multiple_gms(
            self,
            campaign,
            user_profile1,
            user_profile2,
            user_profile3,
            gm_membership1,
            gm_membership2,
            player_membership1,
            gm_persona1,
            gm_persona2,
            player_persona1,
        ):
            """Successfully leave a campaign when just a player. The entrustee is not specified, and there are multiple GMs. So the GM that will be entrusted should be the one with the oldest membership."""
            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            player_membership1_id = player_membership1.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            player_persona1_id = player_persona1.id

            # Leave the campaign without specifying the entrustee
            services.leave_campaign(member=user_profile3, campaign=campaign)

            # Assert campaign has not been deleted
            assert Campaign.objects.filter(id=campaign_id).exists()

            # Assert the leaving gm's campaign membership is deleted
            assert not CampaignMembership.objects.filter(
                id=player_membership1_id
            ).exists()

            # Refresh the personas
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            player_persona1.refresh_from_db()

            # Assert the leaving player's personas have been entrusted to the first gm
            assert Persona.objects.filter(id=player_persona1_id).exists()
            assert player_persona1.member.id == gm_membership1_id
            assert player_persona1.type == Persona.PersonaType.PLAYER
            assert player_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the first gm's personas remain
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership1_id
            assert gm_persona1.type == Persona.PersonaType.GM
            assert gm_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the second gm's personas remain
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_leave_campaign_player_multiple_character_personas(
            self,
            campaign,
            user_profile1,
            user_profile3,
            gm_membership1,
            player_membership1,
            gm_persona1,
            player_persona1,
            npc_persona1,
            character_persona1,
            character_persona3,
            retired_persona11,
            retired_persona12,
        ):
            """Successfully leave a campaign when just a player. The entrustee is not specified, and there are multiple GMs. So the GM that will be entrusted should be the one with the oldest membership."""
            campaign_id = campaign.id
            gm_membership1_id = gm_membership1.id
            player_membership1_id = player_membership1.id
            gm_persona1_id = gm_persona1.id
            player_persona1_id = player_persona1.id
            npc_persona1_id = npc_persona1.id
            character_persona3_id = character_persona3.id
            retired_persona11_id = retired_persona11.id
            retired_persona12_id = retired_persona12.id

            # Leave the campaign without specifying the entrustee
            services.leave_campaign(member=user_profile3, campaign=campaign)

            # Assert campaign has not been deleted
            assert Campaign.objects.filter(id=campaign_id).exists()

            # Assert the leaving gm's campaign membership is deleted
            assert not CampaignMembership.objects.filter(
                id=player_membership1_id
            ).exists()

            # Refresh the personas
            gm_persona1.refresh_from_db()
            player_persona1.refresh_from_db()
            npc_persona1.refresh_from_db()
            character_persona1.refresh_from_db()
            character_persona3.refresh_from_db()
            retired_persona11.refresh_from_db()
            retired_persona12.refresh_from_db()

            # Assert the leaving player's personas have been entrusted to the first gm
            assert Persona.objects.filter(id=player_persona1_id).exists()
            assert player_persona1.member.id == gm_membership1_id
            assert player_persona1.type == Persona.PersonaType.PLAYER
            assert player_persona1.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=character_persona3_id).exists()
            assert character_persona3.member.id == gm_membership1_id
            assert character_persona3.type == Persona.PersonaType.CHARACTER
            assert character_persona3.status == Persona.PersonaStatus.RETIRED

            # Assert the first gm's personas remain
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership1_id
            assert gm_persona1.type == Persona.PersonaType.GM
            assert gm_persona1.status == Persona.PersonaStatus.ACTIVE
            assert Persona.objects.filter(id=npc_persona1_id).exists()
            assert npc_persona1.member.id == gm_membership1_id
            assert npc_persona1.type == Persona.PersonaType.NPC
            assert npc_persona1.status == Persona.PersonaStatus.ACTIVE
            assert Persona.objects.filter(id=retired_persona11_id).exists()
            assert retired_persona11.member.id == gm_membership1_id
            assert retired_persona11.type == Persona.PersonaType.CHARACTER
            assert retired_persona11.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=retired_persona12_id).exists()
            assert retired_persona12.member.id == gm_membership1_id
            assert retired_persona12.type == Persona.PersonaType.NPC
            assert retired_persona12.status == Persona.PersonaStatus.RETIRED

    @pytest.mark.failure
    class TestFailure:
        def test_leave_campaign_non_member(
            self, campaign, user_profile1, gm_membership1, gm_persona1, user_profile2
        ):
            """Raise an error when a user that is not a member of the campaign tries to leave the campaign."""
            with pytest.raises(UserNotMemberError):
                services.leave_campaign(member=user_profile2, campaign=campaign)

        def test_leave_campaign_last_gm_with_players(
            self,
            campaign,
            user_profile1,
            user_profile3,
            user_profile4,
            gm_membership1,
            player_membership1,
            player_membership2,
            gm_persona1,
            player_persona1,
            player_persona2,
        ):
            """Raise an error when the last GM of the campaign tries to leave the campaign."""
            with pytest.raises(LastGMCannotLeaveError):
                services.leave_campaign(member=user_profile1, campaign=campaign)


class TestPromoteToGM:
    """Tests for promote_to_gm function."""

    @pytest.mark.success
    class TestSuccess:
        def test_promote_only_member_persona(
            self,
            campaign,
            user_profile1,
            user_profile3,
            gm_membership1,
            player_membership1,
            gm_persona1,
            player_persona1,
        ):
            """Successfully promote a player to GM when the player has only a member_persona."""
            player_membership1_id = player_membership1.id
            player_persona1_id = player_persona1.id

            services.promote_to_gm(member=user_profile3, campaign=campaign)

            # Refresh the persona
            player_persona1.refresh_from_db()

            # Assert the player's persona has been promoted to GM
            assert Persona.objects.filter(id=player_persona1_id).exists()
            assert player_persona1.member.id == player_membership1_id
            assert player_persona1.type == Persona.PersonaType.GM
            assert player_persona1.status == Persona.PersonaStatus.ACTIVE

        def test_promote_multiple_personas(
            self,
            campaign,
            user_profile1,
            user_profile3,
            gm_membership1,
            player_membership1,
            gm_persona1,
            player_persona1,
            character_persona3,
        ):
            """Successfully promote a player to GM when the player has multiple personas."""
            player_membership1_id = player_membership1.id
            player_persona1_id = player_persona1.id
            character_persona3_id = character_persona3.id

            services.promote_to_gm(member=user_profile3, campaign=campaign)

            # Refresh the persona
            player_persona1.refresh_from_db()
            character_persona3.refresh_from_db()

            # Assert the player's member_persona has been promoted to GM
            assert Persona.objects.filter(id=player_persona1_id).exists()
            assert player_persona1.member.id == player_membership1_id
            assert player_persona1.type == Persona.PersonaType.GM
            assert player_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the player's other personas remain
            assert Persona.objects.filter(id=character_persona3_id).exists()
            assert character_persona3.member.id == player_membership1_id
            assert character_persona3.type == Persona.PersonaType.CHARACTER
            assert character_persona3.status == Persona.PersonaStatus.ACTIVE

    @pytest.mark.failure
    class TestFailure:
        def test_promote_non_member(
            self, campaign, user_profile1, user_profile2, gm_membership1, gm_persona1
        ):
            """Raise error when promoting a player to GM where the user is not a member of the campaign."""
            with pytest.raises(UserNotMemberError):
                services.promote_to_gm(member=user_profile2, campaign=campaign)

        def test_promote_already_gm(
            self, campaign, user_profile1, gm_membership1, gm_persona1
        ):
            """Raise error when promoting a member to GM where the member is already a GM."""
            with pytest.raises(MemberAlreadyGMError):
                services.promote_to_gm(member=user_profile1, campaign=campaign)


class TestDemoteToPlayer:
    """Tests for demote_to_player function."""

    @pytest.mark.success
    class TestSuccess:
        def test_demote_non_sole_gm_entrustee_not_specified(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
            npc_persona1,
        ):
            """Successfully demote a GM to a player when the entrustee is not specified. The enstrustee should be the oldest GM."""
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            npc_persona1_id = npc_persona1.id

            # Create additional GM
            extra_gm_user = User.objects.create_user(
                username="extra_user", password="extra"
            )
            extra_gm_user_profile = UserProfile.objects.create(
                user=extra_gm_user, display_name="Extra GM"
            )
            extra_gm_membership = CampaignMembership.objects.create(
                campaign=campaign,
                user=extra_gm_user_profile,
                role=CampaignMembership.CampaignRoles.GM,
            )
            extra_gm_persona = Persona.objects.create(
                member=extra_gm_membership,
                type=Persona.PersonaType.GM,
                status=Persona.PersonaStatus.ACTIVE,
                name="Extra GM",
                description="Extra GM",
            )

            # Demote the first gm to player
            services.demote_to_player(member=user_profile1, campaign=campaign)

            # Refresh membership and personas
            gm_membership1.refresh_from_db()
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            npc_persona1.refresh_from_db()

            # Assert membership has been demoted
            assert CampaignMembership.objects.filter(id=gm_membership1_id).exists()
            assert gm_membership1.role == CampaignMembership.CampaignRoles.PLAYER

            # Assert member_persona has been demoted
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership1_id
            assert gm_persona1.type == Persona.PersonaType.PLAYER
            assert gm_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the NPC persona has been retired to the second gm
            assert Persona.objects.filter(id=npc_persona1_id).exists()
            assert npc_persona1.member.id == gm_membership2_id
            assert npc_persona1.type == Persona.PersonaType.NPC
            assert npc_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the first gm continue to have its personas
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_demote_non_sole_gm_character_persona(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
            npc_persona1,
            character_persona1,
        ):
            """Successfully demote a GM to a player when the GM has character personas."""
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            npc_persona1_id = npc_persona1.id
            character_persona1_id = character_persona1.id

            # Demote the first gm to player
            services.demote_to_player(
                member=user_profile1, entrustee=user_profile2, campaign=campaign
            )

            # Refresh membership and personas
            gm_membership1.refresh_from_db()
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            npc_persona1.refresh_from_db()
            character_persona1.refresh_from_db()

            # Assert membership has been demoted
            assert CampaignMembership.objects.filter(id=gm_membership1_id).exists()
            assert gm_membership1.role == CampaignMembership.CampaignRoles.PLAYER

            # Assert member_persona has been demoted
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership1_id
            assert gm_persona1.type == Persona.PersonaType.PLAYER
            assert gm_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the NPC persona has been retired to the second gm
            assert Persona.objects.filter(id=npc_persona1_id).exists()
            assert npc_persona1.member.id == gm_membership2_id
            assert npc_persona1.type == Persona.PersonaType.NPC
            assert npc_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the character persona remains with the first gm
            assert Persona.objects.filter(id=character_persona1_id).exists()
            assert character_persona1.member.id == gm_membership1_id
            assert character_persona1.type == Persona.PersonaType.CHARACTER
            assert character_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the first gm continue to have its personas
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

        def test_demote_non_sole_gm_entrusted_personas(
            self,
            campaign,
            user_profile1,
            user_profile2,
            gm_membership1,
            gm_membership2,
            gm_persona1,
            gm_persona2,
            npc_persona1,
            retired_persona11,
            retired_persona12,
        ):
            """Successfully demote a GM to a player when the GM has character personas."""
            gm_membership1_id = gm_membership1.id
            gm_membership2_id = gm_membership2.id
            gm_persona1_id = gm_persona1.id
            gm_persona2_id = gm_persona2.id
            npc_persona1_id = npc_persona1.id
            retired_persona11_id = retired_persona11.id
            retired_persona12_id = retired_persona12.id

            # Demote the first gm to player
            services.demote_to_player(
                member=user_profile1, entrustee=user_profile2, campaign=campaign
            )

            # Refresh membership and personas
            gm_membership1.refresh_from_db()
            gm_persona1.refresh_from_db()
            gm_persona2.refresh_from_db()
            npc_persona1.refresh_from_db()
            retired_persona11.refresh_from_db()
            retired_persona12.refresh_from_db()

            # Assert membership has been demoted
            assert CampaignMembership.objects.filter(id=gm_membership1_id).exists()
            assert gm_membership1.role == CampaignMembership.CampaignRoles.PLAYER

            # Assert member_persona has been demoted
            assert Persona.objects.filter(id=gm_persona1_id).exists()
            assert gm_persona1.member.id == gm_membership1_id
            assert gm_persona1.type == Persona.PersonaType.PLAYER
            assert gm_persona1.status == Persona.PersonaStatus.ACTIVE

            # Assert the NPC persona has been retired to the second gm
            assert Persona.objects.filter(id=npc_persona1_id).exists()
            assert npc_persona1.member.id == gm_membership2_id
            assert npc_persona1.type == Persona.PersonaType.NPC
            assert npc_persona1.status == Persona.PersonaStatus.RETIRED

            # Assert the entrusted personas have been transferred to the second gm
            assert Persona.objects.filter(id=retired_persona11_id).exists()
            assert retired_persona11.member.id == gm_membership2_id
            assert retired_persona11.type == Persona.PersonaType.CHARACTER
            assert retired_persona11.status == Persona.PersonaStatus.RETIRED
            assert Persona.objects.filter(id=retired_persona12_id).exists()
            assert retired_persona12.member.id == gm_membership2_id
            assert retired_persona12.type == Persona.PersonaType.NPC
            assert retired_persona12.status == Persona.PersonaStatus.RETIRED

            # Assert the first gm continue to have its personas
            assert Persona.objects.filter(id=gm_persona2_id).exists()
            assert gm_persona2.member.id == gm_membership2_id
            assert gm_persona2.type == Persona.PersonaType.GM
            assert gm_persona2.status == Persona.PersonaStatus.ACTIVE

    @pytest.mark.failure
    class TestFailure:
        def test_demote_non_member(
            self, campaign, user_profile1, user_profile2, gm_membership1, gm_persona1
        ):
            """Raise error when demoting a player to GM where the user is not a member of the campaign."""
            with pytest.raises(UserNotMemberError):
                services.demote_to_player(member=user_profile2, campaign=campaign)

        def test_demote_already_player(
            self,
            campaign,
            user_profile1,
            user_profile3,
            gm_membership1,
            gm_persona1,
            player_membership1,
            player_persona1,
        ):
            """Raise error when demoting a member to GM where the member is already a player."""
            with pytest.raises(MemberAlreadyPlayerError):
                services.demote_to_player(member=user_profile3, campaign=campaign)


# endregion

# region Integration Tests


class TestCommonFlows:
    """Integration tests for the common flows."""

    def test_full_campaign_flow(self, user_profile1, user_profile2):
        """Test the full user journey though creating and joining a campaign."""
        # region 1. Create the campaign
        campaign = services.create_campaign(
            creator=user_profile1,
            title="Full Flow Campaign",
            description="This campaign is made to test the full user journey.",
        )

        # Assert the campaign has been created
        assert Campaign.objects.filter(id=campaign.id).exists()

        # Assert the campaign variables
        assert campaign.title == "Full Flow Campaign"
        assert (
            campaign.description
            == "This campaign is made to test the full user journey."
        )

        # Assert the GM membership exists
        assert CampaignMembership.objects.filter(
            user=user_profile1,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.GM,
        ).exists()

        # Assert the GM persona exists
        gm_membership = CampaignMembership.objects.filter(
            user=user_profile1, campaign=campaign
        ).get()
        assert Persona.objects.filter(
            member=gm_membership, type=Persona.PersonaType.GM
        ).exists()
        assert gm_membership.member_persona() is not None

        # Assert the GM persona variables
        gm_persona = Persona.objects.filter(member=gm_membership).get()
        assert gm_persona.name == user_profile1.display_name
        assert gm_persona.description == ""
        # endregion

        # region 2. Another User Joins
        player_membership = services.join_campaign(
            campaign=campaign, user=user_profile2
        )

        # Assert the player membership has been created
        assert CampaignMembership.objects.filter(
            user=user_profile2,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        ).exists()

        # Assert the player persona exists
        assert Persona.objects.filter(
            member=player_membership, type=Persona.PersonaType.PLAYER
        ).exists()
        assert player_membership.member_persona() is not None

        # Assert the player persona variables
        player_persona = Persona.objects.filter(member=player_membership).get()
        assert player_persona.name == user_profile2.display_name
        assert player_persona.description == ""
        # endregion

        # region 3. Promote the other user to GM
        services.promote_to_gm(member=user_profile2, campaign=campaign)

        # Refresh the membership and persona
        player_membership.refresh_from_db()
        player_persona.refresh_from_db()

        # Assert the player membership has been promoted to GM
        assert CampaignMembership.objects.filter(
            id=player_membership.id, role=CampaignMembership.CampaignRoles.GM
        ).exists()

        # Assert the other user's persona has been promoted to GM
        assert Persona.objects.filter(
            member=player_membership, type=Persona.PersonaType.GM
        ).exists()
        assert player_membership.member_persona() is not None

        # Assert the other user's persona variables
        assert player_persona.name == user_profile2.display_name
        assert player_persona.description == ""
        # endregion

        # region 4. Original creator leaves the campaign
        services.leave_campaign(member=user_profile1, campaign=campaign)

        # Assert the campaign still exists
        assert Campaign.objects.filter(id=campaign.id).exists()

        # Assert the campaign membership has been deleted
        assert not CampaignMembership.objects.filter(
            user=user_profile1, campaign=campaign
        ).exists()

        # Assert the GM persona has been retired to the other GM
        assert Persona.objects.filter(
            member=player_membership,
            type=Persona.PersonaType.GM,
            status=Persona.PersonaStatus.RETIRED,
        ).exists()
        # endregion


# endregion

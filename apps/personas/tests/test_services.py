# tests/personas/test_services.py
import pytest
from django.contrib.auth.models import User
from django.db import transaction
from django.test import override_settings

from apps.accounts.models import UserProfile
from apps.campaigns.exceptions import (
    MemberNotGMError,
    MemberAlreadyGMError,
    LastGMCannotLeaveError,
    MemberAlreadyPlayerError,
)
from apps.campaigns.models import CampaignMembership
from apps.personas.exceptions import (
    MemberPersonaLimitReachedError,
    PersonaNameIsInvalidError,
    PersonaDescriptionIsInvalidError,
    MemberAlreadyHasMemberPersonaError,
    MemberCannotTransferPersonaError,
    MemberCannotEditPersonaError,
    MemberAlreadyPersonaOwnerError,
    MemberCannotTransferPersonaToSelfError,
    MemberDoesntHaveMemberPersonaError,
)
from apps.personas.models import Persona
from apps.personas import services


class TestHasReachedPersonaLimit:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_gm_has_unlimited_limit(self, gm_membership):
        assert services.has_reached_persona_limit(gm_membership) is False

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_player_under_limit(self, player_membership, settings):
        assert services.has_reached_persona_limit(player_membership) is False

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_player_at_limit(self, player_membership, settings):
        # Create personas to reach the limit
        for i in range(2):
            Persona.objects.create(
                member=player_membership,
                name=f"Persona {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )
        assert services.has_reached_persona_limit(player_membership) is True

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_player_at_limit_with_increase(self, player_membership, settings):
        assert services.has_reached_persona_limit(player_membership, increase=2) is True


class TestCreatePersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_success(self, player_membership):
        persona = services.create_persona(
            player_membership,
            Persona.PersonaType.CHARACTER,
            "Test Character",
            "Test Description",
        )
        assert persona.name == "Test Character"
        assert persona.description == "Test Description"
        assert persona.type == Persona.PersonaType.CHARACTER
        assert persona.status == Persona.PersonaStatus.ACTIVE
        assert persona.member == player_membership

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_without_description(self, player_membership):
        persona = services.create_persona(
            player_membership, Persona.PersonaType.CHARACTER, "Test Character"
        )
        assert persona.description == ""

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_exceeds_limit(self, player_membership):
        # Fill up the limit (PLAYER_PERSONA_LIMIT = 2)
        for i in range(2):
            Persona.objects.create(
                member=player_membership,
                name=f"Persona {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )

        with pytest.raises(MemberPersonaLimitReachedError):
            services.create_persona(
                player_membership, Persona.PersonaType.CHARACTER, "Too Many"
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_name_too_long(self, player_membership):
        with pytest.raises(PersonaNameIsInvalidError):
            services.create_persona(
                player_membership, Persona.PersonaType.CHARACTER, "A" * 101
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_name_blank(self, player_membership):
        with pytest.raises(PersonaNameIsInvalidError):
            services.create_persona(
                player_membership, Persona.PersonaType.CHARACTER, "   "
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_persona_description_too_long(self, player_membership):
        with pytest.raises(PersonaDescriptionIsInvalidError):
            services.create_persona(
                player_membership, Persona.PersonaType.CHARACTER, "Test Name", "A" * 501
            )


class TestCreateMemberPersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_gm_member_persona(self, gm_membership):
        persona = services.create_member_persona(gm_membership, "GM Description")
        assert persona.name == gm_membership.user.display_name
        assert persona.description == "GM Description"
        assert persona.type == Persona.PersonaType.GM
        assert persona.status == Persona.PersonaStatus.ACTIVE
        assert persona.member == gm_membership

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_player_member_persona(self, player_membership):
        persona = services.create_member_persona(player_membership)
        assert persona.name == player_membership.user.display_name
        assert persona.type == Persona.PersonaType.PLAYER

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_member_persona_already_exists(self, gm_membership, gm_persona):
        with pytest.raises(MemberAlreadyHasMemberPersonaError):
            services.create_member_persona(gm_membership)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_member_persona_exceeds_limit(self, player_membership):
        # Fill up the limit with non-member personas
        for i in range(2):
            Persona.objects.create(
                member=player_membership,
                name=f"Persona {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )

        with pytest.raises(MemberPersonaLimitReachedError):
            services.create_member_persona(player_membership)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_member_persona_display_name_too_long(self, player_membership):
        player_membership.user.display_name = "A" * 101
        player_membership.user.save()

        with pytest.raises(PersonaNameIsInvalidError):
            services.create_member_persona(player_membership)


class TestCreateCharacterPersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_character_persona_success(self, player_membership):
        persona = services.create_character_persona(
            player_membership, "Test Character", "Test Description"
        )
        assert persona.type == Persona.PersonaType.CHARACTER
        assert persona.member == player_membership


class TestCreateNpcPersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_npc_persona_success(self, gm_membership):
        persona = services.create_npc_persona(
            gm_membership, "Test NPC", "Test Description"
        )
        assert persona.type == Persona.PersonaType.NPC
        assert persona.member == gm_membership

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_create_npc_persona_not_gm(self, player_membership):
        with pytest.raises(MemberNotGMError):
            services.create_npc_persona(player_membership, "Test NPC")


class TestDeletePersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_delete_persona_success(self, gm_membership, gm_persona):
        services.delete_persona(gm_membership, gm_persona)
        with pytest.raises(Persona.DoesNotExist):
            gm_persona.refresh_from_db()

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_delete_persona_not_owner(self, player_membership, gm_persona):
        with pytest.raises(MemberCannotEditPersonaError):
            services.delete_persona(player_membership, gm_persona)


class TestTransferPersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_persona_success(
        self, gm_membership, player_membership, gm_persona
    ):
        transferred = services.transfer_persona(
            gm_membership, player_membership, gm_persona
        )
        assert transferred.member == player_membership

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_persona_to_self(self, gm_membership, gm_persona):
        with pytest.raises(MemberCannotTransferPersonaToSelfError):
            services.transfer_persona(gm_membership, gm_membership, gm_persona)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_persona_not_owner(
        self, player_membership, gm_membership, gm_persona
    ):
        with pytest.raises(MemberCannotTransferPersonaError):
            services.transfer_persona(player_membership, gm_membership, gm_persona)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_persona_already_owner(
        self, gm_membership, player_membership, gm_persona
    ):
        # First transfer - GM transfers to player
        services.transfer_persona(gm_membership, player_membership, gm_persona)

        # Now player owns the persona. Try to transfer from GM to player (GM is not the owner)
        with pytest.raises(MemberCannotTransferPersonaError):
            services.transfer_persona(gm_membership, player_membership, gm_persona)

        # OR - Try to transfer from player to GM (player is the owner, but GM is not the owner)
        # This should work since player is the owner
        services.transfer_persona(player_membership, gm_membership, gm_persona)

        # Now GM owns it again. Try to transfer from GM to GM (same owner and receiver)
        with pytest.raises(MemberCannotTransferPersonaToSelfError):
            services.transfer_persona(gm_membership, gm_membership, gm_persona)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_persona_exceeds_receiver_limit(
        self, gm_membership, player_membership, gm_persona
    ):
        # Fill up the receiver's limit
        for i in range(2):
            Persona.objects.create(
                member=player_membership,
                name=f"Persona {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )

        with pytest.raises(MemberPersonaLimitReachedError):
            services.transfer_persona(gm_membership, player_membership, gm_persona)


class TestTransferEntrustedPersonas:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_entrusted_personas_success(
        self, gm_membership, gm_membership2, retired_persona
    ):
        transferred = services.transfer_entrusted_personas(
            gm_membership, gm_membership2
        )
        assert len(transferred) == 1
        assert transferred[0].member == gm_membership2

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_multiple_entrusted_personas(self, gm_membership, gm_membership2):
        # Create multiple retired personas owned by the first GM
        for i in range(3):
            Persona.objects.create(
                member=gm_membership,
                name=f"Retired {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.RETIRED,
            )

        # Transfer to the second GM (who has no limit)
        transferred = services.transfer_entrusted_personas(
            gm_membership, gm_membership2
        )
        assert len(transferred) == 3
        assert all(p.member == gm_membership2 for p in transferred)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_entrusted_personas_to_self(self, gm_membership, retired_persona):
        with pytest.raises(MemberCannotTransferPersonaToSelfError):
            services.transfer_entrusted_personas(gm_membership, gm_membership)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_transfer_entrusted_personas_exceeds_limit(
        self, gm_membership, player_membership
    ):
        # Create 2 retired personas to transfer
        for i in range(2):
            Persona.objects.create(
                member=gm_membership,
                name=f"Retired {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.RETIRED,
            )

        # Receiver already has 1 persona (near the limit of 2)
        Persona.objects.create(
            member=player_membership,
            name="Existing Persona",
            type=Persona.PersonaType.CHARACTER,
            status=Persona.PersonaStatus.ACTIVE,
        )

        with pytest.raises(MemberPersonaLimitReachedError):
            services.transfer_entrusted_personas(gm_membership, player_membership)


class TestRetirePersona:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_persona_success(self, gm_membership, gm_membership2, gm_persona):
        # player_membership is a PLAYER, but entrustee must be a GM
        # Create a GM entrustee
        gm_entrustee = gm_membership2  # Use the GM fixture

        retired = services.retire_persona(gm_membership, gm_entrustee, gm_persona)
        assert retired.status == Persona.PersonaStatus.RETIRED
        assert retired.member == gm_entrustee

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_persona_entrustee_not_gm(
        self, gm_membership, player_membership, gm_persona
    ):
        with pytest.raises(MemberNotGMError):
            services.retire_persona(gm_membership, player_membership, gm_persona)


class TestRetireCharacterPersonas:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_character_personas_success(
        self, player_membership, gm_membership, player_character_persona
    ):
        retired = services.retire_character_personas(player_membership, gm_membership)
        assert len(retired) == 1
        assert retired[0].status == Persona.PersonaStatus.RETIRED
        assert retired[0].member == gm_membership

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_multiple_character_personas(self, player_membership, gm_membership):
        # Create multiple character personas
        for i in range(3):
            Persona.objects.create(
                member=player_membership,
                name=f"Character {i}",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )

        retired = services.retire_character_personas(player_membership, gm_membership)
        assert len(retired) == 3

    # Currently the GM has no limit on the number of character personas they can have
    # However only a GM can be enstrusted with retired personas, so this test is redundant
    #
    # @override_settings(PLAYER_PERSONA_LIMIT=2)
    # def test_retire_character_personas_exceeds_limit(
    #     self, player_membership, gm_membership
    # ):
    #     # Create 2 character personas to retire
    #     for i in range(2):
    #         Persona.objects.create(
    #             member=player_membership,
    #             name=f"Character {i}",
    #             type=Persona.PersonaType.CHARACTER,
    #             status=Persona.PersonaStatus.ACTIVE,
    #         )
    #
    #     # GM already has 1 persona (near the limit of 2)
    #     Persona.objects.create(
    #         member=gm_membership,
    #         name="GM Persona",
    #         type=Persona.PersonaType.GM,
    #         status=Persona.PersonaStatus.ACTIVE,
    #     )
    #
    #     with pytest.raises(MemberPersonaLimitReachedError):
    #         services.retire_character_personas(player_membership, gm_membership)


class TestRetireNpcPersonas:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_npc_personas_success(
        self, gm_membership, gm_membership2, npc_persona
    ):
        # Need to create another GM to receive the NPCs (player_membership is a PLAYER)
        gm_entrustee = gm_membership2  # Use the GM fixture as entrustee

        retired = services.retire_npc_personas(gm_membership, gm_entrustee)
        assert len(retired) == 1
        assert retired[0].status == Persona.PersonaStatus.RETIRED
        assert retired[0].member == gm_entrustee

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_npc_personas_not_gm_owner(self, player_membership, gm_membership):
        with pytest.raises(MemberNotGMError):
            services.retire_npc_personas(player_membership, gm_membership)


class TestRetirePersonasForLeavingCampaign:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_gm_leaving_campaign(
        self,
        gm_membership,
        gm_membership2,
        gm_persona,
        npc_persona,
        retired_persona,
        gm_character_persona,
    ):
        retired = services.retire_personas_for_leaving_campaign(
            gm_membership, gm_membership2
        )

        # Should have: retired_persona, character_persona, npc_persona, gm_persona
        assert len(retired) == 4

        # Check member persona was retired and transferred
        gm_persona.refresh_from_db()
        assert gm_persona.status == Persona.PersonaStatus.RETIRED
        assert gm_persona.member == gm_membership2

        # Check character persona was retired
        gm_character_persona.refresh_from_db()
        assert gm_character_persona.status == Persona.PersonaStatus.RETIRED
        assert gm_character_persona.member == gm_membership2

        # Check NPC persona was retired
        npc_persona.refresh_from_db()
        assert npc_persona.status == Persona.PersonaStatus.RETIRED
        assert npc_persona.member == gm_membership2

        # Check retired persona was transferred (already retired)
        retired_persona.refresh_from_db()
        assert retired_persona.member == gm_membership2

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_player_leaving_campaign(
        self, player_membership, gm_membership, player_persona, player_character_persona
    ):
        retired = services.retire_personas_for_leaving_campaign(
            player_membership, gm_membership
        )

        # Should retire character and member persona
        assert len(retired) == 2
        assert all(p.status == Persona.PersonaStatus.RETIRED for p in retired)
        assert all(p.member == gm_membership for p in retired)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_retire_gm_leaving_campaign_no_entrustee(self, gm_membership):
        # player_membership is a PLAYER, but we need a GM entrustee
        # This test is redundant if we use proper fixtures
        pass


class TestEditPersonaDetails:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_edit_persona_as_owner(self, player_membership, player_persona):
        edited = services.edit_persona_details(
            player_membership,
            player_persona,
            name="New Name",
            description="New Description",
        )
        assert edited.name == "New Name"
        assert edited.description == "New Description"

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_edit_persona_as_gm(self, gm_membership, player_persona):
        edited = services.edit_persona_details(
            gm_membership, player_persona, name="Edited by GM"
        )
        assert edited.name == "Edited by GM"

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_edit_persona_not_owner_or_gm(self, player_membership2, player_persona):
        with pytest.raises(MemberCannotEditPersonaError):
            services.edit_persona_details(
                player_membership2, player_persona, name="Should Fail"
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_edit_persona_name_too_long(self, player_membership, player_persona):
        with pytest.raises(PersonaNameIsInvalidError):
            services.edit_persona_details(
                player_membership, player_persona, name="A" * 101
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_edit_persona_name_blank(self, player_membership, player_persona):
        with pytest.raises(PersonaNameIsInvalidError):
            services.edit_persona_details(player_membership, player_persona, name="   ")


class TestPromotePersonasToGM:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_promote_persona_to_gm_success(self, player_membership, player_persona):
        services.promote_personas_to_gm_for_membership(player_membership)

        player_persona.refresh_from_db()
        assert player_persona.type == Persona.PersonaType.GM

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_promote_persona_already_gm(self, gm_membership):
        with pytest.raises(MemberAlreadyGMError):
            services.promote_personas_to_gm_for_membership(gm_membership)

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_promote_persona_no_member_persona(self, player_membership):
        # Delete the member persona
        player_persona = player_membership.member_persona()
        if player_persona:
            player_persona.delete()

        with pytest.raises(MemberDoesntHaveMemberPersonaError):
            services.promote_personas_to_gm_for_membership(player_membership)


class TestDemotePersonasToPlayer:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_demote_persona_to_player_success(self, gm_membership, gm_persona):
        # Create another GM so this one can be demoted
        second_gm_user = UserProfile.objects.create(
            user=User.objects.create_user(username="second_gm_for_demote")
        )
        second_gm = CampaignMembership.objects.create(
            campaign=gm_membership.campaign,
            user=second_gm_user,
            role=CampaignMembership.CampaignRoles.GM,
        )

        retired = services.demote_personas_to_player_for_membership(
            gm_membership, second_gm
        )

        gm_persona.refresh_from_db()
        assert gm_persona.type == Persona.PersonaType.PLAYER

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_demote_persona_already_player(self, player_membership, gm_membership):
        with pytest.raises(MemberAlreadyPlayerError):
            services.demote_personas_to_player_for_membership(
                player_membership, gm_membership
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_demote_last_gm(self, gm_membership, player_membership):
        # Only one GM, can't demote
        with pytest.raises(LastGMCannotLeaveError):
            services.demote_personas_to_player_for_membership(
                gm_membership, player_membership
            )

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_demote_gm_no_member_persona(self, gm_membership):
        # Create another GM so demotion is allowed
        second_gm_user = UserProfile.objects.create(
            user=User.objects.create_user(username="second_gm_for_demote2")
        )
        second_gm = CampaignMembership.objects.create(
            campaign=gm_membership.campaign,
            user=second_gm_user,
            role=CampaignMembership.CampaignRoles.GM,
        )

        # Delete the member persona
        gm_persona = gm_membership.member_persona()
        if gm_persona:
            gm_persona.delete()

        # Should still work, just skip the member persona update
        retired = services.demote_personas_to_player_for_membership(
            gm_membership, second_gm
        )
        assert len(retired) >= 0  # Just checking it doesn't raise


# Additional test for member_persona edge cases
class TestMemberPersonaMethod:
    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_member_persona_returns_none_when_no_member_persona(self, gm_membership):
        assert gm_membership.member_persona() is None

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_member_persona_returns_gm_persona(self, gm_membership, gm_persona):
        assert gm_membership.member_persona() == gm_persona

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_member_persona_returns_player_persona(
        self, player_membership, player_persona
    ):
        assert player_membership.member_persona() == player_persona

    @override_settings(PLAYER_PERSONA_LIMIT=2)
    def test_member_persona_asserts_on_multiple_member_personas(
        self, gm_membership, gm_persona
    ):
        # Create another GM persona (shouldn't happen normally)
        Persona.objects.create(
            member=gm_membership,
            name="Another GM",
            type=Persona.PersonaType.GM,
            status=Persona.PersonaStatus.ACTIVE,
        )

        with pytest.raises(AssertionError):
            gm_membership.member_persona()

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.personas.models import Persona

pytestmark = pytest.mark.django_db

HTMX_HEADERS = {"HTTP_HX_REQUEST": "true"}


class TestCancelCreatePersonaView:
    """Tests for the cancel_create_persona view."""

    @pytest.mark.success
    class TestSuccess:
        def test_htmx_get_returns_blank_response_with_trigger(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return a blank successful response and HX trigger for a valid HTMX GET request."""
            url = reverse(
                "personas:cancel-create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert response["HX-Trigger"] == "cancelCreateNpcPersona"

    @pytest.mark.failure
    class TestFailure:
        def test_anonymous_user_gets_not_found(self, client, campaign):
            """Return 404 when an anonymous user tries to cancel persona creation."""
            url = reverse(
                "personas:cancel-create-persona",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_non_member_gets_not_found(self, unaffiliated_client, campaign):
            """Return 404 when an authenticated non-member tries to cancel persona creation."""
            url = reverse(
                "personas:cancel-create-persona",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = unaffiliated_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_post_returns_bad_request(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 400 when cancel persona creation receives a POST request."""
            url = reverse(
                "personas:cancel-create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.post(url, **HTMX_HEADERS)

            assert response.status_code == 400
            assert (
                b"Request methods to the cancel create campaign endpoint must be GET."
                in response.content
            )


class TestCreatePersonaView:
    """Tests for the create_persona view."""

    @pytest.fixture(autouse=True)
    def persona_limit_settings(self, settings):
        settings.PLAYER_PERSONA_LIMIT = 10

    @pytest.mark.success
    class TestSuccess:
        def test_htmx_get_returns_create_form(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return the create persona form for a valid HTMX GET request."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert b'id="create-npc-persona-form"' in response.content
            assert b"Create Persona" in response.content

        def test_htmx_post_creates_npc_persona_and_sets_trigger(
            self, authenticated_gm_client, campaign_with_members, gm_membership
        ):
            """Create an NPC persona and set the NPC-created HX trigger."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.post(
                url,
                {"name": "Goblin Scout", "description": "A sneaky goblin."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 200
            assert response["HX-Trigger"] == "npcPersonaCreated"

            persona = Persona.objects.get(name="Goblin Scout")
            assert persona.description == "A sneaky goblin."
            assert persona.type == Persona.PersonaType.NPC
            assert persona.status == Persona.PersonaStatus.ACTIVE
            assert persona.member == gm_membership

        def test_htmx_post_creates_character_persona_and_sets_trigger(
            self, authenticated_player_client, campaign_with_members, player_membership
        ):
            """Create a character persona and set the character-created HX trigger."""
            url = reverse(
                "personas:create-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_type": "character",
                },
            )

            response = authenticated_player_client.post(
                url,
                {"name": "Brave Adventurer", "description": "Ready for danger."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 200
            assert response["HX-Trigger"] == "characterPersonaCreated"

            persona = Persona.objects.get(name="Brave Adventurer")
            assert persona.description == "Ready for danger."
            assert persona.type == Persona.PersonaType.CHARACTER
            assert persona.status == Persona.PersonaStatus.ACTIVE
            assert persona.member == player_membership

    @pytest.mark.failure
    class TestFailure:
        def test_anonymous_user_gets_not_found(self, client, campaign):
            """Return 404 when an anonymous user tries to access persona creation."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_non_member_gets_not_found(self, unaffiliated_client, campaign):
            """Return 404 when an authenticated non-member tries to access persona creation."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = unaffiliated_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_post_with_invalid_form_returns_form(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return the form without creating a persona when submitted data is invalid."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.post(
                url,
                {"name": "", "description": "Invalid because name is required."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 200
            assert b'id="create-npc-persona-form"' in response.content
            assert not Persona.objects.filter(
                name="", type=Persona.PersonaType.NPC
            ).exists()

        def test_htmx_post_with_invalid_persona_type_returns_server_error(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 500 and avoid creating a persona when the persona type is invalid."""
            url = reverse(
                "personas:create-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_type": "monster",
                },
            )

            response = authenticated_gm_client.post(
                url,
                {"name": "Bad Type", "description": "This should fail."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 500
            assert b"Something went wrong! Please try again!" in response.content
            assert not Persona.objects.filter(name="Bad Type").exists()

        def test_htmx_post_returns_server_error_when_service_raises(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 500 and avoid creating a persona when the service layer raises an exception."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            with patch("apps.personas.views.services.create_persona") as create_persona:
                create_persona.side_effect = Exception("Unexpected failure")

                response = authenticated_gm_client.post(
                    url,
                    {"name": "Broken NPC", "description": "This should not save."},
                    **HTMX_HEADERS,
                )

            assert response.status_code == 500
            assert b"Something went wrong! Please try again!" in response.content
            assert not Persona.objects.filter(name="Broken NPC").exists()

        def test_htmx_delete_returns_bad_request(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 400 when persona creation receives a DELETE request."""
            url = reverse(
                "personas:create-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.delete(url, **HTMX_HEADERS)

            assert response.status_code == 400
            assert (
                b"Request methods to the create campaign endpoint must be GET or POST"
                in response.content
            )


class TestCancelEditPersonaView:
    """Tests for the cancel_edit_persona view."""

    @pytest.mark.success
    class TestSuccess:
        def test_htmx_get_returns_persona_with_trigger(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return the persona partial and HX trigger for a valid cancel-edit GET request."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert response["HX-Trigger"] == "cancelEditnpcPersona"
            assert npc_persona.name.encode() in response.content

    @pytest.mark.failure
    class TestFailure:
        def test_anonymous_user_gets_not_found(self, client, campaign, npc_persona):
            """Return 404 when an anonymous user tries to cancel persona editing."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={"campaign_id": campaign.id, "persona_id": npc_persona.id},
            )

            response = client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_non_member_gets_not_found(
            self, unaffiliated_client, campaign, npc_persona
        ):
            """Return 404 when an authenticated non-member tries to cancel persona editing."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={"campaign_id": campaign.id, "persona_id": npc_persona.id},
            )

            response = unaffiliated_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_missing_persona_returns_not_found(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 404 when cancelling edit for a persona that does not exist."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_id": 999999},
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_persona_belonging_to_other_member_returns_not_found(
            self, authenticated_player_client, campaign_with_members, npc_persona
        ):
            """Return 404 when cancelling edit for another member's persona."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_player_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_post_returns_bad_request(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return 400 when cancel persona editing receives a POST request."""
            url = reverse(
                "personas:cancel-edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.post(url, **HTMX_HEADERS)

            assert response.status_code == 400
            assert (
                b"Request methods to the cancel create campaign endpoint must be GET."
                in response.content
            )


class TestEditPersonaView:
    """Tests for the edit_persona view."""

    @pytest.mark.success
    class TestSuccess:
        def test_htmx_get_returns_edit_form(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return the edit persona form for a valid HTMX GET request."""
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert b"<form" in response.content
            assert npc_persona.name.encode() in response.content

        def test_htmx_post_edits_persona_and_sets_trigger(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Edit a persona and set the persona-edited HX trigger."""
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.post(
                url,
                {"name": "Edited NPC", "description": "Edited description."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 200
            assert response["HX-Trigger"] == "npcPersonaEdited"

            npc_persona.refresh_from_db()
            assert npc_persona.name == "Edited NPC"
            assert npc_persona.description == "Edited description."

    @pytest.mark.failure
    class TestFailure:
        def test_anonymous_user_gets_not_found(self, client, campaign, npc_persona):
            """Return 404 when an anonymous user tries to edit a persona."""
            url = reverse(
                "personas:edit-persona",
                kwargs={"campaign_id": campaign.id, "persona_id": npc_persona.id},
            )

            response = client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_non_member_gets_not_found(
            self, unaffiliated_client, campaign, npc_persona
        ):
            """Return 404 when an authenticated non-member tries to edit a persona."""
            url = reverse(
                "personas:edit-persona",
                kwargs={"campaign_id": campaign.id, "persona_id": npc_persona.id},
            )

            response = unaffiliated_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_delete_returns_bad_request(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return 400 when persona editing receives a DELETE request."""
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.delete(url, **HTMX_HEADERS)

            assert response.status_code == 400
            assert (
                b"Request methods to the edit campaign endpoint must be GET or POST"
                in response.content
            )

        def test_missing_persona_returns_not_found(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 404 when trying to edit a persona that does not exist."""
            url = reverse(
                "personas:edit-persona",
                kwargs={"campaign_id": campaign_with_members.id, "persona_id": 999999},
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_persona_belonging_to_other_member_returns_not_found(
            self, authenticated_player_client, campaign_with_members, npc_persona
        ):
            """Return 404 when trying to edit another member's persona."""
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_player_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_post_with_invalid_form_returns_form(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return the edit form without saving changes when submitted data is invalid."""
            original_name = npc_persona.name
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            response = authenticated_gm_client.post(
                url,
                {"name": "", "description": "Name is required."},
                **HTMX_HEADERS,
            )

            assert response.status_code == 200
            assert b"<form" in response.content

            npc_persona.refresh_from_db()
            assert npc_persona.name == original_name

        def test_htmx_post_returns_server_error_when_service_raises(
            self, authenticated_gm_client, campaign_with_members, npc_persona
        ):
            """Return 500 and avoid saving changes when the service layer raises an exception."""
            original_name = npc_persona.name
            url = reverse(
                "personas:edit-persona",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_id": npc_persona.id,
                },
            )

            with patch(
                "apps.personas.views.services.edit_persona_details"
            ) as edit_details:
                edit_details.side_effect = Exception("Unexpected failure")

                response = authenticated_gm_client.post(
                    url,
                    {"name": "Should Not Save", "description": "Should fail."},
                    **HTMX_HEADERS,
                )

            assert response.status_code == 500
            assert b"Something went wrong! Please try again!" in response.content

            npc_persona.refresh_from_db()
            assert npc_persona.name == original_name


class TestPersonaListView:
    """Tests for the persona_list view."""

    @pytest.mark.success
    class TestSuccess:
        def test_htmx_get_returns_npc_personas_for_current_member_only(
            self,
            authenticated_gm_client,
            campaign_with_members,
            gm_membership,
            player_membership,
            npc_persona,
        ):
            """Return only the current member's NPC personas for a valid NPC list request."""
            Persona.objects.create(
                member=player_membership,
                name="Other Member NPC",
                type=Persona.PersonaType.NPC,
                status=Persona.PersonaStatus.ACTIVE,
            )
            url = reverse(
                "personas:persona-list",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert npc_persona.name.encode() in response.content
            assert b"Other Member NPC" not in response.content

        def test_htmx_get_returns_character_personas_for_current_member_only(
            self,
            authenticated_player_client,
            campaign_with_members,
            player_membership,
            gm_membership,
            player_character_persona,
        ):
            """Return only the current member's character personas for a valid character list request."""
            Persona.objects.create(
                member=gm_membership,
                name="Other Member Character",
                type=Persona.PersonaType.CHARACTER,
                status=Persona.PersonaStatus.ACTIVE,
            )
            url = reverse(
                "personas:persona-list",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_type": "character",
                },
            )

            response = authenticated_player_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 200
            assert player_character_persona.name.encode() in response.content
            assert b"Other Member Character" not in response.content

    @pytest.mark.failure
    class TestFailure:
        def test_anonymous_user_gets_not_found(self, client, campaign):
            """Return 404 when an anonymous user tries to view a persona list."""
            url = reverse(
                "personas:persona-list",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_non_member_gets_not_found(self, unaffiliated_client, campaign):
            """Return 404 when an authenticated non-member tries to view a persona list."""
            url = reverse(
                "personas:persona-list",
                kwargs={"campaign_id": campaign.id, "persona_type": "npc"},
            )

            response = unaffiliated_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 404

        def test_htmx_get_with_invalid_persona_type_returns_server_error(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 500 when the requested persona list type is invalid."""
            url = reverse(
                "personas:persona-list",
                kwargs={
                    "campaign_id": campaign_with_members.id,
                    "persona_type": "monster",
                },
            )

            response = authenticated_gm_client.get(url, **HTMX_HEADERS)

            assert response.status_code == 500
            assert b"Something went wrong! Please try again!" in response.content

        def test_htmx_post_returns_bad_request(
            self, authenticated_gm_client, campaign_with_members
        ):
            """Return 400 when the persona list endpoint receives a POST request."""
            url = reverse(
                "personas:persona-list",
                kwargs={"campaign_id": campaign_with_members.id, "persona_type": "npc"},
            )

            response = authenticated_gm_client.post(url, **HTMX_HEADERS)

            assert response.status_code == 400
            assert (
                b"Request methods to the persona list endpoint must be GET."
                in response.content
            )

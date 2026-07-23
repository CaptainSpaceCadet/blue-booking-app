"""
Persona service layer for business logic.

This module contains service functions that handle campaign-related operations.
All functions expect validated input and raise appropriate exceptions for
invalid operations.

TODO:
- has_reached_persona_limit x
- create_persona x
- create_member_persona x
- create_player_persona x
- create_npc_persona
- delete_persona x
- transfer_persona x
- transfer_entrusted_personas
- retire_persona x
- retire_character_personas_for_membership x
- retire_npc_personas_for_membership x
- retire_personas_for_leaving_campaign x
- edit_persona_details x
- promote_personas_to_gm_for_membership x
- demote_personas_to_player_for_membership x
"""

from typing import List
from django.conf import settings
from django.db import transaction

from apps.accounts.models import UserProfile
from apps.campaigns.exceptions import (
    MemberNotGMError,
    MemberAlreadyGMError,
    MemberAlreadyPlayerError,
    LastGMCannotLeaveError,
)
from apps.campaigns.models import CampaignMembership
from apps.personas.exceptions import (
    MemberPersonaLimitReachedError,
    PersonaNameIsInvalidError,
    PersonaDescriptionIsInvalidError,
    MemberAlreadyHasMemberPersonaError,
    MemberCannotTransferPersonaError,
    MemberCannotEditPersonaError,
    PersonaWithPostsDeletionError,
    MemberAlreadyPersonaOwnerError,
    MemberCannotTransferPersonaToSelfError,
    MemberDoesntHaveMemberPersonaError,
)
from apps.personas.models import Persona


def has_reached_persona_limit(
    membership: CampaignMembership, increase: int = 0
) -> bool:
    """
    Query how many personas a member has within a campaign and determine if the limit has been reached.

    GM members have an unlimited persona limit, while players have a set persona limit determined by settings.py.

    If the persona limit has been reached, return True and the member should not be able to create a new persona.

    :param membership: CampaignMembership of the member to check
    :param increase: The increase in persona count
    :return: True, if the persona limit has been reached, False otherwise
    """

    if membership.role == CampaignMembership.CampaignRoles.GM:
        return False

    return membership.personas.count() + increase >= settings.PLAYER_PERSONA_LIMIT


@transaction.atomic
def create_persona(
    creator: CampaignMembership,
    persona_type: Persona.PersonaType,
    name: str,
    description: str | None = None,
) -> Persona:
    """
    Create a new persona for a member. The member will own this persona. The persona can be a member persona, such as GM or PLAYER but also a fantasy persona such as CHARACTER or NPC.

    :param persona_type: PersonaType of the persona
    :param creator: CampaignMembership of the member to create a new persona
    :param name: Name of the persona, it must be less than 100 characters
    :param description: Description of the persona, it must be less than 500 characters
    :return: The created Persona

    :raises MemberPersonaLimitReachedError: If the member has reached their persona limit
    :raises PersonaNameIsInvalidError: If the name is greater than 100 characters, or blank
    :raises PersonaDescriptionIsInvalidError: If the description is more than 500 characters
    """

    if has_reached_persona_limit(creator):
        raise MemberPersonaLimitReachedError()

    if len(name) > 100:
        raise PersonaNameIsInvalidError("Name must be less than 100 characters.")
    if description is not None and len(description) > 500:
        raise PersonaDescriptionIsInvalidError(
            "Description must be less than 500 characters."
        )
    if not name.strip():
        raise PersonaNameIsInvalidError("Name must not be blank.")

    if description is None:
        description = ""

    return Persona.objects.create(
        member=creator,
        status=Persona.PersonaStatus.ACTIVE,
        type=persona_type,
        name=name,
        description=description,
    )


@transaction.atomic
def create_member_persona(
    member: CampaignMembership, description: str | None = None
) -> Persona:
    """
    Create the singular member persona for a member. This persona will be a GM if the member is a GM, or it will be a PLAYER if the member is a PLAYER.

    This function is typically called when a User joins a campaign and a CampaignMembership is created.

    By default, the persona title will be set to the User's display name. And will be updated when the User changes their display name.

    :param member: CampaignMembership of the member
    :param description: Description of the persona, it must be less than 500 characters
    :return: The created member persona

    :raises MemberAlreadyHasMemberPersonaError: If the member already has a member persona
    :raises MemberPersonaLimitReachedError: If the member has reached their persona limit, under normal circumstances and scope this should be impossible to reach
    :raises PersonaNameIsInvalidError: If the display name is greater than 100 characters, or blank, this should be caught by the accounts' service layer
    :raises PersonaDescriptionIsInvalidError: If the description is more than 500 characters
    """

    if member.member_persona() is not None:
        raise MemberAlreadyHasMemberPersonaError()

    if has_reached_persona_limit(member):
        raise MemberPersonaLimitReachedError()

    if len(member.user.display_name) > 100:
        raise PersonaNameIsInvalidError(
            "Persona name is derived from display name and must be less than 100 characters."
        )

    if description is not None and len(description) > 500:
        raise PersonaDescriptionIsInvalidError(
            "Description must be less than 500 characters."
        )

    if member.role == CampaignMembership.CampaignRoles.GM:
        return create_persona(
            member, Persona.PersonaType.GM, member.user.display_name, description
        )

    if member.role == CampaignMembership.CampaignRoles.PLAYER:
        return create_persona(
            member, Persona.PersonaType.PLAYER, member.user.display_name, description
        )

    # Should be impossible to reach, but just in case
    raise ValueError(f"Invalid role: {member.role}")


@transaction.atomic
def create_character_persona(
    creator: CampaignMembership, name: str, description: str | None = None
):
    """
    Create a player character persona for a member.

    :param creator: CampaignMembership of the member to create a new persona
    :param name: Name of the persona, it must be less than 100 characters
    :param description: Description of the persona, it must be less than 500 characters
    :return: The created Persona
    """
    return create_persona(creator, Persona.PersonaType.CHARACTER, name, description)


@transaction.atomic
def create_npc_persona(
    creator: CampaignMembership, name: str, description: str | None = None
) -> Persona:
    """
    Create a non-player character persona for a GM.

    :param creator: CampaignMembership of the GM to create a new persona
    :param name: Name of the persona, it must be less than 100 characters
    :param description: Description of the persona, it must be less than 500 characters
    :return: The created Persona
    """

    if creator.role != CampaignMembership.CampaignRoles.GM:
        raise MemberNotGMError()

    return create_persona(
        creator,
        Persona.PersonaType.NPC,
        name,
        description,
    )


@transaction.atomic
def delete_persona(deleter: CampaignMembership, persona: Persona) -> None:
    """
    Delete the persona, as instigated by the deleter.

    Deleter must be the owner of the persona, and the persona must not be the author of any posts. If the persona is the author of any posts, the persona should instead be transferred to a GM using the retire_persona service.

    :param deleter: CampaignMembership of the member that is deleting the persona
    :param persona: Persona of the deleter to delete

    :raises: MemberCannotDeletePersona: If the deleter is not the owner of the persona
    :raises: PersonaWithPostsDeletionError: If the persona has active posts it cannot be deleted
    """

    if deleter != persona.member:
        raise MemberCannotEditPersonaError()

    # TODO: Check if the persona has active posts, if so, raise an error
    if False:
        raise PersonaWithPostsDeletionError()

    persona.delete()


@transaction.atomic
def transfer_persona(
    owner: CampaignMembership, receiver: CampaignMembership, persona: Persona
) -> Persona:
    """
    Transfer ownership and control of a persona to another member.

    Owner must be the owner of the persona, and the receiver must not be the owner of the persona. Additionally, in receiving the persona, the receiver must not have reached their persona limit.

    :param owner: The owner of the persona, who is attempting to transfer it to another member
    :param receiver: The member that will receive the persona
    :param persona: The persona to transfer
    :return: The transferred persona

    :raises: MemberCannotTransferPersonaError: If the member attempting to transfer is not the owner of the persona
    :raises: MemberAlreadyPersonaOwnerError: If the receiver is already the owner of the persona
    :raises: MemberPersonaLimitReachedError: If the receiver has reached their persona limit
    """

    if owner == receiver:
        raise MemberCannotTransferPersonaToSelfError()

    if owner != persona.member:
        raise MemberCannotTransferPersonaError()

    if receiver == persona.member:
        raise MemberAlreadyPersonaOwnerError()

    if has_reached_persona_limit(receiver):
        raise MemberPersonaLimitReachedError()

    persona.member = receiver
    persona.save()

    return persona


@transaction.atomic
def transfer_entrusted_personas(
    member: CampaignMembership, receiver: CampaignMembership
) -> List[Persona]:
    """
    Transfer all entrusted personas to another member. Entrusted personas are those marked as "RETIRED".

    **WARNING**: This function will not check if the receiver is a GM.

    :param member: The member who is attempting to transfer all of their entrusted personas to another member
    :param receiver: The member that will receive the retired personas
    :return: The list of personas that were transferred

    :raises: MemberPersonaLimitReachedError: If the receiver has reached their persona limit
    """

    if member == receiver:
        raise MemberCannotTransferPersonaToSelfError()

    personas = Persona.objects.filter(
        member=member, status=Persona.PersonaStatus.RETIRED
    )
    transferred_personas = []

    if has_reached_persona_limit(receiver, personas.count()):
        raise MemberPersonaLimitReachedError()

    for persona in personas:
        if member != persona.member:
            raise MemberCannotTransferPersonaError()

    for persona in personas:
        # There is probably a better way to transfer many personas at once, but this is fine for now
        # maybe can use the .update() method to update many personas at once?
        transferred_personas.append(transfer_persona(member, receiver, persona))

    return transferred_personas


@transaction.atomic
def retire_persona(
    owner: CampaignMembership, entrustee: CampaignMembership, persona: Persona
) -> Persona:
    """
    If a member wishes to delete a persona, but the persona cannot be deleted due to already owning posts, they can instead retire the persona by transferring it to a GM entrustee.

    The entrustee must be a GM, and the entrustee must not be the owner of the persona. Additionally, the entrustee must not have reached their persona limit.

    The status of the persona will be set to "RETIRED".

    :param owner: The owner of the persona, who is attempting to retire it
    :param entrustee: The GM member that will take over responsibility for the persona
    :param persona: The persona to retire
    :return: The retired persona

    :raises: MemberCannotTransferPersonaError: If the member attempting to transfer is not the owner of the persona
    :raises: MemberAlreadyPersonaOwnerError: If the entrustee is already the owner of the persona
    :raises: UserNotGMError: If the entrustee is not a GM
    :raises: MemberPersonaLimitReachedError: If the entrustee has reached their persona limit
    """

    if entrustee.role != CampaignMembership.CampaignRoles.GM:
        raise MemberNotGMError()

    persona.status = Persona.PersonaStatus.RETIRED
    transfer_persona(owner, entrustee, persona)
    return persona


@transaction.atomic
def retire_character_personas(
    membership: CampaignMembership, entrustee: CampaignMembership
) -> List[Persona]:
    """
    Retire all active non-member personas for a member.

    This does not handle the retired personas that the member has been entrusted.

    The status of the personas will be set to "RETIRED".

    :param membership: The member that is retiring their character personas
    :param entrustee: The GM member that will take over responsibility for the personas
    :return: The list of personas that were retired

    :raises: UserNotGMError: If the entrustee is not a GM
    :raises: MemberPersonaLimitReachedError: If the entrustee has reached their persona limit
    """

    personas = Persona.objects.filter(
        member=membership,
        status=Persona.PersonaStatus.ACTIVE,
        type=Persona.PersonaType.CHARACTER,
    )
    retired_personas = []

    if has_reached_persona_limit(entrustee, personas.count()):
        raise MemberPersonaLimitReachedError()

    for persona in personas:
        retired_personas.append(retire_persona(membership, entrustee, persona))

    return retired_personas


@transaction.atomic
def retire_npc_personas(
    membership: CampaignMembership, entrustee: CampaignMembership
) -> List[Persona]:
    """
    Retire all active NPC personas for a GM member.

    This does not handle the retired personas that the member has been entrusted.

    The status of the personas will be set to "RETIRED".

    :param membership: The member that is retiring their npc personas
    :param entrustee: The GM member that will take over responsibility for the personas
    :return: The list of personas that were retired

    :raises: UserNotGMError: If the member or entrustee is not a GM
    :raises: MemberPersonaLimitReachedError: If the entrustee has reached their persona limit
    """

    if membership.role != CampaignMembership.CampaignRoles.GM:
        raise MemberNotGMError()

    personas = Persona.objects.filter(
        member=membership,
        status=Persona.PersonaStatus.ACTIVE,
        type=Persona.PersonaType.NPC,
    )
    retired_personas = []

    if has_reached_persona_limit(entrustee, personas.count()):
        raise MemberPersonaLimitReachedError()

    for persona in personas:
        retired_personas.append(retire_persona(membership, entrustee, persona))

    return retired_personas


@transaction.atomic
def retire_personas_for_leaving_campaign(
    membership: CampaignMembership, entrustee: CampaignMembership
) -> List[Persona]:
    """
    Retire or transfer all personas for a member so that the member can leave the campaign.

    - If the member is a GM, transfer all entrusted personas to the entrustee.
    - Retire all active CHARACTER personas for the member.
    - If the member is a GM, retire all active NPC personas.
    - Retire the member persona.

    :param membership: The member that is retiring their npc personas
    :param entrustee: The GM member that will take over responsibility for the personas
    :return: The list of personas that were retired

    :raises: UserNotGMError: If the entrustee is not a GM
    :raises: MemberPersonaLimitReachedError: If the entrustee has reached their persona limit
    """

    retired_personas = []

    # Transfer all entrusted personas
    if membership.role == CampaignMembership.CampaignRoles.GM:
        retired_personas.extend(transfer_entrusted_personas(membership, entrustee))

    # Retire all active character personas
    retired_personas.extend(retire_character_personas(membership, entrustee))

    # Retire all active NPC personas
    if membership.role == CampaignMembership.CampaignRoles.GM:
        retired_personas.extend(retire_npc_personas(membership, entrustee))

    if membership.member_persona() is None:
        raise MemberDoesntHaveMemberPersonaError()
    # Retire the member persona
    retired_personas.append(
        retire_persona(membership, entrustee, membership.member_persona())
    )

    return retired_personas


@transaction.atomic
def edit_persona_details(
    editor: CampaignMembership,
    persona: Persona,
    name: str | None = None,
    description: str | None = None,
) -> Persona:
    """
    Edit the details of a persona. The name and description can be changed.

    :param editor: The member that is editing the persona, they must be the owner or a GM
    :param persona: The persona to edit
    :param name: The new name of the persona
    :param description: The new description of the persona
    :return: The edited persona

    :raises: MemberCannotEditPersonaError: If the editor is not the owner or a GM of the persona
    :raises: PersonaNameIsInvalidError: If the name is greater than 100 characters
    :raises: PersonaDescriptionIsInvalidError: If the description is more than 500 characters
    """

    if editor != persona.member and editor.role != CampaignMembership.CampaignRoles.GM:
        raise MemberCannotEditPersonaError()

    if name is not None and len(name) > 100:
        raise PersonaNameIsInvalidError("Name must be less than 100 characters.")
    if description is not None and len(description) > 500:
        raise PersonaDescriptionIsInvalidError(
            "Description must be less than 500 characters."
        )
    if name is not None and not name.strip():
        raise PersonaNameIsInvalidError("Name must not be blank.")

    if name is not None:
        persona.name = name
    if description is not None:
        persona.description = description
    persona.save()

    return persona


@transaction.atomic
def promote_personas_to_gm_for_membership(membership: CampaignMembership) -> None:
    """
    Handle the changes to the personas when a member is promoted to a GM.

    - Change the member persona from a PLAYER persona to a GM persona.

    :param membership: The member that is being promoted to a GM

    :raises MemberAlreadyGMError: If the member is already a GM of the campaign
    """

    if membership.role == CampaignMembership.CampaignRoles.GM:
        raise MemberAlreadyGMError()

    member_persona = membership.member_persona()
    if member_persona is None:
        raise MemberDoesntHaveMemberPersonaError()
    member_persona.type = Persona.PersonaType.GM
    member_persona.save()


@transaction.atomic
def demote_personas_to_player_for_membership(
    membership: CampaignMembership, entrustee: CampaignMembership
) -> List[Persona]:
    """
    Handle the transfer of personas when a member is demoted to a player

    1. All entrusted personas will be transferred to the entrustee.
    2. The NPC personas will be retired to the entrustee.
    2. The member persona will be demoted to a PLAYER persona.

    :param membership: The GM that is being demoted to a player
    :param entrustee: The GM that will take over responsibility for the personas
    :return: The list of personas that were transferred

    :raises MemberAlreadyPlayerError: If the member is already a PLAYER of the campaign
    :raises LastGMCannotLeaveError: If the member is the last GM of the campaign, they can't be demoted
    :raises: UserNotGMError: If the entrustee is not a GM
    :raises MemberPersonaLimitReachedError: If the entrustee has reached their persona limit
    """

    if membership.role == CampaignMembership.CampaignRoles.PLAYER:
        raise MemberAlreadyPlayerError()

    if membership.is_last_gm():
        raise LastGMCannotLeaveError()

    if entrustee.role != CampaignMembership.CampaignRoles.GM:
        raise MemberNotGMError()

    retired_personas = []

    retired_personas.extend(transfer_entrusted_personas(membership, entrustee))
    retired_personas.extend(retire_npc_personas(membership, entrustee))

    member_persona = membership.member_persona()
    if member_persona is not None:
        member_persona.type = Persona.PersonaType.PLAYER
        member_persona.save()

    return retired_personas

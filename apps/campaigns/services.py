"""
Campaign service layer for business logic.

This module contains service functions that handle campaign-related operations.
All functions expect validated input and raise appropriate exceptions for
invalid operations.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from apps.accounts.models import UserProfile
from apps.campaigns.models import CampaignMembership, Campaign
from apps.campaigns.exceptions import (
    UserCampaignMembershipLimitReachedError,
    UserNotMemberError,
    MemberNotSoleGMError,
    LastGMCannotLeaveError,
    CampaignMembershipFullError,
    UserAlreadyMemberError,
    MemberAlreadyGMError,
    MemberAlreadyPlayerError,
    CampaignTitleIsInvalidError,
    CampaignDescriptionIsInvalidError,
    MemberNotGMError,
)
from apps.personas.models import Persona
from apps.personas.services import (
    create_member_persona,
    retire_personas_for_leaving_campaign,
    promote_personas_to_gm_for_membership,
    demote_personas_to_player_for_membership,
)
from blue_booking_app.settings import USER_CAMPAIGN_LIMIT, CAMPAIGN_MEMBER_LIMIT


def has_reached_campaign_limit(user: UserProfile) -> bool:
    """
    Query how many campaigns a user is a member of, and determine if the user campaign membership limit been_reached.

    If the campaign membership limit has been reached, this function will return True and the user should not be able
    to join another campaign.

    :param user: UserProfile of the user to check
    :return: True if user has reached the limit, False otherwise
    """

    campaign_count = CampaignMembership.objects.filter(user=user).count()
    return campaign_count >= USER_CAMPAIGN_LIMIT


def is_campaign_membership_full(campaign: Campaign) -> bool:
    """
    Query how many members a campaign has, and determine if the campaign membership is full.

    If the campaign is full, this function will return True and a new user should not be able to join a campaign.

    :param campaign: Campaign of the campaign to check
    :return: True if campaign membership is full, False otherwise
    """

    member_count = CampaignMembership.objects.filter(campaign=campaign).count()
    return member_count >= CAMPAIGN_MEMBER_LIMIT


# TODO: when adding initial gm create member persona for them: DONE
@transaction.atomic
def create_campaign(
    creator: UserProfile, title: str, description: str | None
) -> Campaign:
    """
    Create a new campaign and add the creator to the campaign membership list as a GM.

    Campaign cannot be created if the creator cannot join a new campaign.

    :param creator: UserProfile of the creator
    :param title: Title of the campaign, it must be less than 100 characters
    :param description: Description of the campaign, it must be less than 500 characters
    :return: The created Campaign

    :raises UserCampaignMembershipLimitReachedError: If the creator has maxed out their campaign membership limit
    :raises CampaignTitleIsInvalidError: If the title is greater than 100 characters, or blank
    :raises CampaignDescriptionIsInvalidError: If the description is more than 500 characters
    """

    if has_reached_campaign_limit(creator):
        raise UserCampaignMembershipLimitReachedError()

    if len(title) > 100:
        raise CampaignTitleIsInvalidError("Title must be less than 100 characters.")
    if description is not None and len(description) > 500:
        raise CampaignDescriptionIsInvalidError(
            "Description must be less than 500 characters."
        )

    if not title.strip():
        raise CampaignTitleIsInvalidError("Title must not be blank.")

    campaign = Campaign.objects.create(title=title, description=description)

    # Add creator to campaign membership list as GM
    member = CampaignMembership.objects.create(
        campaign=campaign, user=creator, role=CampaignMembership.CampaignRoles.GM
    )

    # Create initial member persona for creator
    create_member_persona(member)

    return campaign


@transaction.atomic
def delete_campaign(deleter: UserProfile, campaign: Campaign) -> None:
    """
    Delete the campaign, as instigated by the deleter.

    Deleter must have full control over the campaign so they must be the sole GM.

    :param deleter: UserProfile of the deleter, they must have GM campaign membership
    :param campaign: Campaign of the campaign to delete

    :raises MemberNotSoleGMError: If the deleter is not a sole GM of the campaign
    """

    if not CampaignMembership.objects.filter(user=deleter, campaign=campaign).exists():
        raise MemberNotSoleGMError()

    deleter_membership = CampaignMembership.objects.get(user=deleter, campaign=campaign)

    if not deleter_membership.is_last_gm():
        raise MemberNotSoleGMError(
            "To delete a campaign, the user must be the only GM."
        )

    campaign.delete()


@transaction.atomic
def edit_campaign(
    editor: UserProfile,
    campaign: Campaign,
    title: str | None = None,
    description: str | None = None,
) -> Campaign:
    """
    Edit the campaign details.

    Editor must be a GM of the campaign.

    :param editor: UserProfile of the editor, they must be a GM of the campaign
    :param campaign: Campaign of the campaign to edit
    :param title: Title of the campaign, it must be less than 100 characters
    :param description: Description of the campaign, it must be less than 500 characters
    :return: The campaign that was edited

    :raises MemberNotGMError: If the editor is not a GM of the campaign
    :raises CampaignTitleIsInvalidError: If the title is greater than 100 characters, or blank
    :raises CampaignDescriptionIsInvalidError: If the description is more than 500 characters
    """

    if not CampaignMembership.objects.filter(
        user=editor, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
    ).exists():
        raise MemberNotGMError()

    if title is not None and len(title) > 100:
        raise CampaignTitleIsInvalidError("Title must be less than 100 characters.")
    if description is not None and len(description) > 500:
        raise CampaignDescriptionIsInvalidError(
            "Description must be less than 500 characters."
        )

    if title is not None:
        campaign.title = title
    if description is not None:
        campaign.description = description

    campaign.save()
    return campaign


# TODO: when joining a campaign create member persona for the joiner: DONE
@transaction.atomic
def join_campaign(user: UserProfile, campaign: Campaign) -> CampaignMembership:
    """
    User joins the campaign as a PLAYER.

    The campaign must not be full and the user must not have reached their campaign membership limit.

    :param user: UserProfile of the user to join
    :param campaign: Campaign of the campaign to join
    :return: CampaignMembership of the new member

    :raises UserAlreadyMemberError: If the user is already a member of the campaign
    :raises CampaignMembershipFullError: If the campaign is full
    :raises CampaignMembershipLimitReachedError: If the user has maxed out their campaign membership limit
    """

    if CampaignMembership.objects.filter(user=user, campaign=campaign).exists():
        raise UserAlreadyMemberError()

    if is_campaign_membership_full(campaign):
        raise CampaignMembershipFullError()

    if has_reached_campaign_limit(user):
        raise UserCampaignMembershipLimitReachedError()

    membership = CampaignMembership.objects.create(
        user=user, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
    )

    # Create member persona for joiner
    create_member_persona(membership)

    return membership


# TODO: handle retiring personas when leaving a campaign: DONE
@transaction.atomic
def leave_campaign(
    member: UserProfile, campaign: Campaign, entrustee: UserProfile | None = None
) -> None:
    """
    Member leaves the campaign.

    Member cannot leave if they are the last GM. Before calling this function another member must be promoted to GM.

    **Warning:** If the member is the last member of the campaign, the campaign will be deleted. This is done by: meth:`apps.campaigns.models.CampaignMembership.delete`.

    :param entrustee:
    :param member: UserProfile of the member to leave
    :param campaign: Campaign of the campaign that is being left

    :raises UserNotMemberError: If the member is not a member of the campaign
    :raises LastGMCannotLeaveError: If the member is the last GM of the campaign and there is still players in the campaign, they can't leave
    """

    if not CampaignMembership.objects.filter(user=member, campaign=campaign).exists():
        raise UserNotMemberError()

    membership = CampaignMembership.objects.get(user=member, campaign=campaign)

    if membership.is_last_gm() and not membership.is_last_member():
        raise LastGMCannotLeaveError()

    # If the member is the last GM don't bother with retiring personas
    if membership.is_last_gm() and membership.is_last_member():
        membership.delete()
        return

    # If the member is not the last GM, retire all the leaving GM's personas

    # If entrustee is not provided, find the first gm member remaining
    if entrustee is None:
        try:
            entrustee_membership = (
                CampaignMembership.objects.filter(
                    campaign=campaign, role=CampaignMembership.CampaignRoles.GM
                )
                .exclude(user=member)
                .earliest("created_at")
            )
            entrustee = entrustee_membership.user
        except CampaignMembership.DoesNotExist:
            raise LastGMCannotLeaveError(
                "Cannot find entrustee to transfer personas to."
            )
    else:
        # Get entrustee's membership
        entrustee_membership = CampaignMembership.objects.get(
            user=entrustee, campaign=campaign
        )

    # Retire all personas for the member being left
    retire_personas_for_leaving_campaign(membership, entrustee_membership)

    membership.delete()


# TODO: handle promoting member persona when promoting to GM: DONE
@transaction.atomic
def promote_to_gm(member: UserProfile, campaign: Campaign) -> None:
    """
    Promote the member that has the PLAYER role to the GM role.

    :param member: UserProfile of the member to promote
    :param campaign: Campaign of the campaign

    :raises UserNotMemberError: If the member is not a member of the campaign
    :raises MemberAlreadyGMError: If the member is already a GM of the campaign
    """

    if not CampaignMembership.objects.filter(user=member, campaign=campaign).exists():
        raise UserNotMemberError()

    membership = CampaignMembership.objects.get(user=member, campaign=campaign)

    if membership.role == CampaignMembership.CampaignRoles.GM:
        raise MemberAlreadyGMError()

    # Prepare the personas for the member being promoted
    promote_personas_to_gm_for_membership(membership)

    membership.role = CampaignMembership.CampaignRoles.GM
    membership.save()


# TODO: handle demoting member persona and transferring retired persona to the other GM: DONE
@transaction.atomic
def demote_to_player(
    member: UserProfile, campaign: Campaign, entrustee: UserProfile | None = None
) -> None:
    """
    Demote the member that has the role of GM to the PLAYER role.

    If the member is the last GM in the campaign, they cannot be demoted as a campaign cannot be left without a GM.

    :param member: UserProfile of the member to demote
    :param campaign: Campaign of the campaign

    :raises UserNotMemberError: If the member is not a member of the campaign
    :raises MemberAlreadyPlayerError: If the member is already a PLAYER of the campaign
    :raises LastGMCannotLeaveError: If the member is the last GM of the campaign, they can't be demoted
    """

    if not CampaignMembership.objects.filter(user=member, campaign=campaign).exists():
        raise UserNotMemberError()

    membership = CampaignMembership.objects.get(user=member, campaign=campaign)

    if membership.role == CampaignMembership.CampaignRoles.PLAYER:
        raise MemberAlreadyPlayerError()

    if membership.is_last_gm():
        raise LastGMCannotLeaveError()

    # If entrustee is not provided, find the first gm member remaining
    if entrustee is None:
        try:
            entrustee_membership = (
                CampaignMembership.objects.filter(
                    campaign=campaign, role=CampaignMembership.CampaignRoles.GM
                )
                .exclude(user=member)
                .earliest("created_at")
            )
            entrustee = entrustee_membership.user
        except CampaignMembership.DoesNotExist:
            raise LastGMCannotLeaveError(
                "Cannot find entrustee to transfer personas to."
            )
    else:
        # Get entrustee's membership
        entrustee_membership = CampaignMembership.objects.get(
            user=entrustee, campaign=campaign
        )

    # Demote all personas for the member being demoted
    demote_personas_to_player_for_membership(membership, entrustee_membership)

    membership.role = CampaignMembership.CampaignRoles.PLAYER
    membership.save()

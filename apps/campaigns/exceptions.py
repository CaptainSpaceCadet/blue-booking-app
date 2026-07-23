"""Custom exceptions for campaigns application."""


class CampaignServiceError(Exception):
    """Base exception for campaign service errors."""

    pass


class CampaignTitleIsInvalidError(CampaignServiceError):
    """Raised when a campaign title is invalid."""

    pass


class CampaignDescriptionIsInvalidError(CampaignServiceError):
    """Raised when a campaign description is invalid."""

    pass


class UserAlreadyMemberError(CampaignServiceError):
    """Raised when a user attempts to join a campaign they're already in."""

    pass


class UserNotMemberError(CampaignServiceError):
    """Raised when a user attempts to leave a campaign they're not in."""

    pass


class MemberAlreadyPlayerError(CampaignServiceError):
    """Raised when a member attempts to be demoted to a PLAYER, but they are already a PLAYER."""

    pass


class MemberAlreadyGMError(CampaignServiceError):
    """Raised when a member attempts to be promoted to a GM, but they are already GM."""

    pass


class MemberNotGMError(CampaignServiceError):
    """Raised when a member is expected to be a GM and is not, frequently used regarding permissions."""

    pass


class MemberNotSoleGMError(CampaignServiceError):
    """Raised when a member tries to do an action which requires full control over the campaign (such as delete it) but the user is not the sole GM."""

    pass


class LastGMCannotLeaveError(CampaignServiceError):
    """Raised when the last GM attempts to leave without assigning a new GM."""

    pass


class UserCampaignMembershipLimitReachedError(CampaignServiceError):
    """Raised when the user tries to join a new campaign and surpasses the number of campaigns they are allowed to join."""

    pass


class CampaignMembershipFullError(CampaignServiceError):
    """Raised when a campaign has reached maximum capacity."""

    pass

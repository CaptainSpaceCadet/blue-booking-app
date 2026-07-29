"""Custom exceptions for personas application."""


class PersonaServiceError(Exception):
    """Base exception for persona service errors."""

    pass


class MemberAlreadyHasMemberPersonaError(PersonaServiceError):
    """Raised when a member attempts to create a member new persona, but they already have a member persona."""

    pass


class MemberPersonaLimitReachedError(PersonaServiceError):
    """Raised when a member has reached their persona limit."""

    pass


class PersonaNameIsInvalidError(PersonaServiceError):
    """Raised when a persona name is invalid."""

    pass


class PersonaDescriptionIsInvalidError(PersonaServiceError):
    """Raised when a persona description is invalid."""

    pass


class MemberCannotEditPersonaError(PersonaServiceError):
    """Raised when a member attempts to edit a persona they do not own, or they are not the GM of the persona's campaign."""

    pass


class MemberCannotEditPersonaError(PersonaServiceError):
    """Raised when a member attempts to edit a persona they do not own, or they are not the GM of the persona's campaign."""

    pass


class MemberCannotTransferPersonaError(PersonaServiceError):
    """Raised when a member attempts to transfer ownership of a persona they do not own."""

    pass


class MemberCannotTransferPersonaToSelfError(PersonaServiceError):
    """Raised when a member attempts to transfer ownership of a persona to themselves."""

    pass


class PersonaWithPostsDeletionError(PersonaServiceError):
    """Raised when someone attempts to delete a persona that has active posts."""

    pass


class MemberAlreadyPersonaOwnerError(PersonaServiceError):
    """Raised when a member attempts to transfer ownership of a persona to themselves."""

    pass


class MemberDoesntHaveMemberPersonaError(PersonaServiceError):
    """Raised when a member doesn't have a member persona. This should not occur."""

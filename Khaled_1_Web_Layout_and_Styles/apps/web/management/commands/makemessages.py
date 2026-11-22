"""makemessages that also collects the messages services raise (ValidationFailed("..."), Forbidden("...")…).

Those messages are written in English in the service layer; DomainErrorMiddleware translates them when it shows
them, so the Arabic interface gets Arabic error toasts without every service importing gettext.
"""
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    xgettext_options = makemessages.Command.xgettext_options + [
        "--keyword=ValidationFailed", "--keyword=Forbidden", "--keyword=Conflict", "--keyword=InsufficientQuantity",
        "--keyword=SelfApproval", "--keyword=DomainError", "--keyword=_l", "--keyword=_t",
    ]

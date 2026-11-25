"""Tiny helper so every state machine in Section 7.2 is written the same way.

Each entity declares TRANSITIONS = {from_state: {allowed_to_states}} and calls `move(...)`.
A generic edit can never change a state field: only entity operations call `move` (FR-2.16, FR-9.12).
"""
from .errors import InvalidTransition


def move(obj, field: str, to: str, transitions: dict[str, set[str]]) -> str:
    """Set obj.<field> to `to` if the transition is allowed. Returns the previous state."""
    current = getattr(obj, field)
    allowed = transitions.get(current, set())
    if to not in allowed:
        raise InvalidTransition(f"{type(obj).__name__}: {current} -> {to} is not allowed")
    setattr(obj, field, to)
    return current


def is_terminal(state: str, transitions: dict[str, set[str]]) -> bool:
    return not transitions.get(state)

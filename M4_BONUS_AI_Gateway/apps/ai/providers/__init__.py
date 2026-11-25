"""Provider adapters. Each adapter implements the same methods as the gateway and returns an AIResult.

Add a provider by writing a module with a `Provider` class and registering it here.
"""


def get_provider(name: str):
    if name == "fake":
        from .fake import Provider
    elif name == "anthropic":
        from .anthropic import Provider
    else:
        raise ValueError(f"Unknown AI provider: {name}")
    return Provider()

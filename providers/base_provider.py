from abc import ABC


class BaseProvider(ABC):
    def __init__(self, **config):
        """Initialize the base provider with a configuration dictionary."""
        pass

    def get_credentials(self, *args, **kwargs):
        pass

    def get_token(self, *args, **kwargs):
        pass

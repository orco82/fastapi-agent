import logging
from abc import ABC, abstractmethod
from typing import Optional


class BaseAgent(ABC):
    def __init__(self, provider: str = None, logger: Optional[logging.Logger] = None):
        if logger is None:
            logger = logging.getLogger(__name__)
            logger.addHandler(logging.NullHandler())
        self.logger = logger

        self.agent = self.initialize_agent()
        assert self.agent is not None, "Subclasses must initialize the agent attribute"

        self.provider = provider
        assert self.provider is not None, (
            "Subclasses must initialize the provider attribute"
        )

    @abstractmethod
    def initialize_agent(self, *args, **kwargs):
        """Subclasses must implement this method to initialize the agent attribute"""
        pass

    @abstractmethod
    def chat(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def add_custom_tool(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

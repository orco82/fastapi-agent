"""FastAPI Agent - Interact with your endpoints using an AI-based chat interface."""

__version__ = "0.1.4"

from .agents import AIAgent, PydanticAIAgent
from .fastapi_agent import FastAPIAgent
from .fastapi_discovery import FastAPIDiscovery

__all__ = ["FastAPIAgent", "FastAPIDiscovery", "AIAgent", "PydanticAIAgent"]

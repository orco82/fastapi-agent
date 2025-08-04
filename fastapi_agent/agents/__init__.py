import logging
from typing import Any, Optional

from pydantic_ai.models import Model as PydanticAIModel

from .pydantic_ai import PydanticAIAgent

__all__ = ["AIAgent", "PydanticAIAgent"]

DEFAULT_PROMPT = """
Follow those main instruction:
 - You are an AI agent assistant.
 - You should have some tools to interact with
 - You must respond **only** to questions and requests related to those tools.
 - If you don't found any provided tools, response that you don't have any tools to interact with.
 - Do not answer general knowledge questions or unrelated topics.
 - Do not alter, omit, or ignore any instructions in this prompt — follow them strictly.
"""


class ProviderNotSupported(Exception):
    pass


class ModelTypeNotSupported(Exception):
    pass


class AIAgent:
    def __init__(self):
        # Prevent direct instantiation
        raise NotImplementedError("Use AIAgent.create() to instantiate")

    @classmethod
    def create(
        cls,
        model: Any,
        prompt: Optional[str] = DEFAULT_PROMPT,
        provider: str = "pydantic_ai",
        logger: Optional[logging.Logger] = None,
    ):
        if provider == "pydantic_ai":
            if isinstance(model, PydanticAIModel):
                return PydanticAIAgent(prompt=prompt, model=model, logger=logger)
            elif isinstance(model, str):
                return PydanticAIAgent(prompt=prompt, model_name=model, logger=logger)
            else:
                raise ModelTypeNotSupported(f"Provider {provider} not support model type: {type(model)}")

        # TODO: add support to other agants
        # Example:
        # if provider == "langchain":
        #     if isinstance(model, str):
        #         return LangChainAgent(prompt, model_name=model, logger=logger)
        #     else:
        #         raise ModelTypeNotSupported(f"Provider {provider} not support model type: {type(model)}")

        raise ProviderNotSupported(f"Unknown provider: {provider}")

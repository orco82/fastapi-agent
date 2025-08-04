import logging
from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.models import Model

from .base_agent import BaseAgent


class PydanticAIAgent(BaseAgent):
    """
    AI Assistant class that encapsulates pydantic-ai agent with custom tools
    """

    def __init__(
        self,
        model_name: str = "openai:gpt-4o",
        model: Optional[Model] = None,
        prompt: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the AI assistant with an optional custom model and system prompt.

        Args:
            model_name (str): The model identifier string in the format 'provider:model-id' (e.g., 'openai:gpt-4o'). Used if `model` is not provided.
            model (Optional[Model]): A fully initialized Model instance. If provided, this will be used instead of creating one from `model_name`.
            prompt (Optional[str]): A custom system prompt string. If not provided, a default prompt from AIAgent.
            logger (Optional[logging.Logger]): add logger
        """
        self.provider = "pydantic_ai"
        self.prompt = prompt
        self.model = model or model_name
        # self.agent = self.initialize_agent()
        super().__init__(provider=self.provider, logger=logger)

    def initialize_agent(self):
        """Create the agent with system prompt and model"""
        self.logger.info(f"initialzing agent with {self.model.__class__}")
        return Agent(
            model=self.model,
            system_prompt=self.prompt,
            output_type=str,
        )

    async def chat(self, message: str, history: list = None) -> tuple[str, list]:
        """
        Chat with message history support

        Args:
            message: User message
            history: Previous conversation history

        Returns:
            tuple: (response, updated_history)
        """
        if history is None:
            history = []

        try:
            # Create a new conversation context with history
            # Note: pydantic-ai might expect a different format for message_history
            # This creates a simple conversation state
            conversation_context = "\n".join(
                [
                    f"{msg['role'].title()}: {msg['content']}"
                    for msg in history[-10:]  # Keep last 10 messages for context
                ]
            )

            # Add context to the current message if there's history
            if conversation_context:
                enhanced_message = f"Previous conversation:\n{conversation_context}\n\nCurrent message: {message}"
            else:
                enhanced_message = message

            result = await self.agent.run(enhanced_message)
            response_text = result.output

            # Update history with new message and response
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response_text})

            return response_text, history

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.debug(f"Debug - Exception details: {e}")

            # Still update history even if there was an error
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return error_msg, history

    def add_custom_tool(self, tool_func):
        """
        Add a custom tool to the agent

        Args:
            tool_func: Function decorated with appropriate pydantic-ai tool decorator
        """
        return self.agent.tool(tool_func)

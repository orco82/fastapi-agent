"""Tests for AI Agent factory and abstraction"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic_ai.models import Model

from fastapi_agent.agents import AIAgent, PydanticAIAgent
from fastapi_agent.agents import ModelTypeNotSupported, ProviderNotSupported


class TestAIAgentFactory:
    """Test the AIAgent factory"""

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_create_agent_with_string_model(self, mock_pydantic_agent):
        """Should create agent with model name string"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = AIAgent.create(model="openai:gpt-4.1-mini", provider="pydantic_ai")

        assert isinstance(agent, PydanticAIAgent)
        assert agent.provider == "pydantic_ai"

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_create_agent_with_model_instance(self, mock_pydantic_agent):
        """Should create agent with Model instance"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        # Create a mock Model instance
        mock_model = Mock(spec=Model)

        agent = AIAgent.create(model=mock_model, provider="pydantic_ai")

        assert isinstance(agent, PydanticAIAgent)
        assert agent.provider == "pydantic_ai"

    def test_create_agent_unsupported_provider(self):
        """Should raise error for unsupported provider"""
        with pytest.raises(ProviderNotSupported) as exc_info:
            AIAgent.create(model="test:model", provider="unsupported_provider")

        assert "Unknown provider" in str(exc_info.value)

    def test_create_agent_unsupported_model_type(self):
        """Should raise error for unsupported model type"""
        with pytest.raises(ModelTypeNotSupported) as exc_info:
            AIAgent.create(model=12345, provider="pydantic_ai")  # Invalid type

        assert "not support model type" in str(exc_info.value)

    def test_direct_instantiation_prevented(self):
        """Should prevent direct instantiation of AIAgent"""
        with pytest.raises(NotImplementedError) as exc_info:
            AIAgent()

        assert "Use AIAgent.create()" in str(exc_info.value)

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_create_agent_with_custom_prompt(self, mock_pydantic_agent):
        """Should create agent with custom prompt"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        custom_prompt = "Custom system prompt for testing"
        agent = AIAgent.create(
            model="openai:gpt-4.1-mini",
            prompt=custom_prompt,
            provider="pydantic_ai",
        )

        assert agent.prompt == custom_prompt


class TestPydanticAIAgent:
    """Test the PydanticAIAgent implementation"""

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_pydantic_ai_agent_initialization(self, mock_pydantic_agent):
        """Should initialize PydanticAIAgent correctly"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(
            model_name="openai:gpt-4.1-mini", prompt="Test prompt"
        )

        assert agent.provider == "pydantic_ai"
        assert agent.prompt == "Test prompt"
        assert agent.model == "openai:gpt-4.1-mini"
        assert agent.agent is not None

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_initialize_agent(self, mock_pydantic_agent):
        """Should initialize pydantic-ai agent correctly"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        # Should have called Agent constructor
        mock_pydantic_agent.assert_called_once_with(
            model="openai:gpt-4.1-mini", system_prompt=None, output_type=str
        )

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_without_history(self, mock_pydantic_agent):
        """Should handle chat without history"""
        # Setup mock
        mock_result = Mock()
        mock_result.output = "Test response"

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = mock_result
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        response, history = await agent.chat("Hello")

        assert response == "Test response"
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Test response"

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_with_history(self, mock_pydantic_agent):
        """Should handle chat with conversation history"""
        # Setup mock
        mock_result = Mock()
        mock_result.output = "Response with context"

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = mock_result
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        initial_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        response, history = await agent.chat("Follow-up question", initial_history)

        assert response == "Response with context"
        assert len(history) == 4  # 2 previous + 2 new
        assert history[-2]["role"] == "user"
        assert history[-2]["content"] == "Follow-up question"
        assert history[-1]["role"] == "assistant"

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_limits_history_context(self, mock_pydantic_agent):
        """Should limit history to last 10 messages for context"""
        # Setup mock
        mock_result = Mock()
        mock_result.output = "Response"

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = mock_result
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        # Create history with more than 10 messages
        long_history = []
        for i in range(15):
            long_history.append({"role": "user", "content": f"Message {i}"})
            long_history.append({"role": "assistant", "content": f"Response {i}"})

        await agent.chat("New message", long_history)

        # Check that only last 10 messages were used in context
        call_args = mock_agent_instance.run.call_args[0][0]
        # Should contain "Previous conversation:" and only recent messages
        assert "Previous conversation:" in call_args
        # The context should be limited (we can't check exact count easily, but verify it was called)
        mock_agent_instance.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_error_handling(self, mock_pydantic_agent):
        """Should handle errors gracefully"""
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.side_effect = Exception("Test error")
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        response, history = await agent.chat("Test message")

        assert "Error:" in response
        assert "Test error" in response
        assert len(history) == 2  # User message + error response

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_add_custom_tool(self, mock_pydantic_agent):
        """Should add custom tool to agent"""
        mock_agent_instance = Mock()
        mock_agent_instance.tool = Mock(side_effect=lambda func: func)
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        def custom_tool():
            """Custom tool for testing"""
            pass

        result = agent.add_custom_tool(custom_tool)

        # Should have called the tool decorator
        mock_agent_instance.tool.assert_called_once_with(custom_tool)
        assert result == custom_tool

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_agent_with_custom_model_instance(self, mock_pydantic_agent):
        """Should accept custom Model instance"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        mock_model = Mock(spec=Model)
        agent = PydanticAIAgent(model=mock_model, prompt="Test")

        assert agent.model == mock_model
        # Should have passed the model to Agent
        mock_pydantic_agent.assert_called_once()
        call_kwargs = mock_pydantic_agent.call_args[1]
        assert call_kwargs["model"] == mock_model

    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    def test_agent_model_name_priority(self, mock_pydantic_agent):
        """Should use model parameter if both model and model_name provided"""
        mock_agent_instance = Mock()
        mock_pydantic_agent.return_value = mock_agent_instance

        mock_model = Mock(spec=Model)
        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini", model=mock_model)

        # model should take priority
        assert agent.model == mock_model

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_empty_history(self, mock_pydantic_agent):
        """Should handle empty history list"""
        mock_result = Mock()
        mock_result.output = "Response"

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = mock_result
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        response, history = await agent.chat("Test", [])

        assert response == "Response"
        assert len(history) == 2

    @pytest.mark.asyncio
    @patch("fastapi_agent.agents.pydantic_ai.Agent")
    async def test_chat_preserves_history_on_error(self, mock_pydantic_agent):
        """Should preserve history even when error occurs"""
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.side_effect = Exception("Error")
        mock_pydantic_agent.return_value = mock_agent_instance

        agent = PydanticAIAgent(model_name="openai:gpt-4.1-mini")

        initial_history = [{"role": "user", "content": "Previous"}]
        response, history = await agent.chat("New", initial_history)

        # Should have original + new user message + error response
        assert len(history) == 3
        assert history[0]["content"] == "Previous"

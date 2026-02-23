"""Tests for FastAPI Agent main orchestrator"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from fastapi_agent.fastapi_agent import (
    AgentQuery,
    AgentResponse,
    APIResponse,
    FastAPIAgent,
)


class TestFastAPIAgent:
    """Test the FastAPIAgent class"""

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_agent_initialization(self, mock_ai_agent_class, app_no_auth):
        """Should initialize FastAPI agent with defaults"""
        # Setup mock
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth, model="openai:gpt-4.1-mini")

        assert agent.app == app_no_auth
        assert agent.base_url == "http://localhost:8000"
        assert agent.model == "openai:gpt-4.1-mini"
        assert agent.agent_provider == "pydantic_ai"
        assert agent.verify_api_call is True

        # Should have created AI assistant
        mock_ai_agent_class.create.assert_called_once()

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_agent_initialization_with_auth(
        self, mock_ai_agent_class, app_bearer_auth
    ):
        """Should initialize agent with authentication configuration"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        auth_config = {"Authorization": "Bearer test_token"}
        agent = FastAPIAgent(
            app_bearer_auth, base_url="http://test:8000", auth=auth_config
        )

        assert agent.depends == auth_config
        assert agent.base_url == "http://test:8000"

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_agent_initialization_with_route_filters(
        self, mock_ai_agent_class, app_no_auth
    ):
        """Should initialize agent with route filtering"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(
            app_no_auth,
            ignore_routes=["DELETE:/users/{user_id}"],
            allow_routes=["GET:/users", "POST:/users"],
        )

        assert agent.ignore_routes == ["DELETE:/users/{user_id}"]
        assert agent.allow_routes == ["GET:/users", "POST:/users"]

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_system_prompt_generation(self, mock_ai_agent_class, app_no_auth):
        """Should generate system prompt with API context"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)
        system_prompt = agent.get_system_prompt()

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0

        # Should contain API context
        assert "API" in system_prompt or "api" in system_prompt
        assert "route" in system_prompt.lower() or "endpoint" in system_prompt.lower()

        # Should contain rules
        assert "instruction" in system_prompt.lower()

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_system_prompt_with_auth_dependencies(
        self, mock_ai_agent_class, app_bearer_auth
    ):
        """Should include auth info in system prompt when auth is configured"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(
            app_bearer_auth, auth={"Authorization": "Bearer token"}
        )
        system_prompt = agent.get_system_prompt()

        # Should mention that auth is already included
        assert "Authorization" in system_prompt or "dependencies" in system_prompt.lower()
        assert "included" in system_prompt.lower()

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_system_prompt_with_verify_api_call(
        self, mock_ai_agent_class, app_no_auth
    ):
        """Should include verification instruction when verify_api_call is True"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth, verify_api_call=True)
        system_prompt = agent.get_system_prompt()

        assert "verify" in system_prompt.lower()
        assert "POST" in system_prompt or "PUT" in system_prompt or "DELETE" in system_prompt

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_system_prompt_without_verify_api_call(
        self, mock_ai_agent_class, app_no_auth
    ):
        """Should not require verification when verify_api_call is False"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth, verify_api_call=False)
        system_prompt = agent.get_system_prompt()

        assert "don't need to verify" in system_prompt.lower() or "do not need to verify" in system_prompt.lower()

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_api_context_prompt(self, mock_ai_agent_class, app_no_auth):
        """Should generate API context prompt with routes info"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)
        api_context = agent.get_api_context_prompt()

        assert isinstance(api_context, str)
        assert len(api_context) > 0

        # Should contain OpenAPI info
        assert "API" in api_context

        # Should contain routes
        assert "Route" in api_context or "route" in api_context

        # Should contain base URL
        assert agent.base_url in api_context

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_get_agent_router(self, mock_ai_agent_class, app_no_auth):
        """Should create agent router with endpoints"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)
        router = agent.get_agent_router()

        # Should have routes (with /agent prefix)
        routes = [route.path for route in router.routes]
        assert "/agent/query" in routes
        assert "/agent/chat" in routes

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_router_without_auth_dependencies(self, mock_ai_agent_class, app_no_auth):
        """Should create router without auth dependencies when auth is None"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth, auth=None)
        router = agent.get_agent_router()

        # Find the query route (with /agent prefix)
        query_route = next((r for r in router.routes if r.path == "/agent/query"), None)
        assert query_route is not None

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_router_with_auth_dependencies(
        self, mock_ai_agent_class, app_bearer_auth
    ):
        """Should create router with auth dependencies when auth is configured"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(
            app_bearer_auth, auth={"Authorization": "Bearer token"}
        )
        router = agent.get_agent_router()

        # Router should be created successfully
        assert router is not None

    @pytest.mark.asyncio
    @patch("fastapi_agent.fastapi_agent.AIAgent")
    async def test_chat_method(self, mock_ai_agent_class, app_no_auth):
        """Should process chat messages through AI agent"""
        mock_assistant = AsyncMock()
        mock_assistant.chat.return_value = ("Test response", [])
        mock_assistant.add_custom_tool = Mock(side_effect=lambda func: func)  # Fix warning
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)

        response, history = await agent.chat("What endpoints are available?")

        assert response == "Test response"
        assert isinstance(history, list)
        mock_assistant.chat.assert_called_once()

    @pytest.mark.asyncio
    @patch("fastapi_agent.fastapi_agent.AIAgent")
    async def test_chat_with_history(self, mock_ai_agent_class, app_no_auth):
        """Should handle chat with conversation history"""
        mock_assistant = AsyncMock()
        mock_assistant.chat.return_value = ("Response", [{"role": "user", "content": "test"}])
        mock_assistant.add_custom_tool = Mock(side_effect=lambda func: func)  # Fix warning
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)

        initial_history = [{"role": "user", "content": "Previous message"}]
        response, history = await agent.chat("New message", history=initial_history)

        assert response == "Response"
        assert len(history) > 0
        mock_assistant.chat.assert_called_with("New message", initial_history)

    @pytest.mark.asyncio
    @patch("fastapi_agent.fastapi_agent.AIAgent")
    async def test_verify_dependencies_success(self, mock_ai_agent_class, app_bearer_auth):
        """Should verify dependencies successfully when auth matches"""
        import json

        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        auth_config = {"Authorization": "Bearer token"}
        agent = FastAPIAgent(app_bearer_auth, auth=auth_config)

        # Should not raise exception
        await agent.verify_dependencies(auth=json.dumps(auth_config))

    @pytest.mark.asyncio
    @patch("fastapi_agent.fastapi_agent.AIAgent")
    async def test_verify_dependencies_failure(self, mock_ai_agent_class, app_bearer_auth):
        """Should raise HTTPException when auth doesn't match"""
        import json
        from fastapi import HTTPException

        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        auth_config = {"Authorization": "Bearer token"}
        agent = FastAPIAgent(app_bearer_auth, auth=auth_config)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await agent.verify_dependencies(auth=json.dumps({"wrong": "auth"}))

        assert exc_info.value.status_code == 401

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_api_request_tool_registration(self, mock_ai_agent_class, app_no_auth):
        """Should register api_request tool with agent"""
        mock_assistant = Mock()
        mock_assistant.add_custom_tool = Mock(side_effect=lambda func: func)
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth)

        # Tool should be registered
        mock_assistant.add_custom_tool.assert_called_once()

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_include_router_flag(self, mock_ai_agent_class, app_no_auth):
        """Should include router in app when include_router is True"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        # Get initial route count
        initial_routes = len(app_no_auth.routes)

        agent = FastAPIAgent(app_no_auth, include_router=True)

        # Should have added routes
        assert len(app_no_auth.routes) > initial_routes

    def test_agent_query_model(self):
        """Should create AgentQuery model correctly"""
        query = AgentQuery(query="test query", history=[])

        assert query.query == "test query"
        assert query.history == []

    def test_agent_response_model(self):
        """Should create AgentResponse model correctly"""
        response = AgentResponse(
            query="test query",
            response="test response",
            status="success",
            history=[],
        )

        assert response.query == "test query"
        assert response.response == "test response"
        assert response.status == "success"
        assert response.error is None

    def test_api_response_model(self):
        """Should create APIResponse model correctly"""
        response = APIResponse(
            status_code=200,
            data={"message": "success"},
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 200
        assert response.data == {"message": "success"}
        assert response.error is None

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_custom_logo_url(self, mock_ai_agent_class, app_no_auth):
        """Should allow custom logo URL"""
        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        custom_logo = "https://example.com/logo.png"
        agent = FastAPIAgent(app_no_auth, logo_url=custom_logo)

        assert agent.logo_url == custom_logo

    @patch("fastapi_agent.fastapi_agent.AIAgent")
    def test_debug_logging(self, mock_ai_agent_class, app_no_auth):
        """Should set debug logging when debug=True"""
        import logging

        mock_assistant = Mock()
        mock_ai_agent_class.create.return_value = mock_assistant

        agent = FastAPIAgent(app_no_auth, debug=True)

        assert agent.logger.level == logging.DEBUG

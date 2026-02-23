"""Tests for route discovery in FastAPI Agent"""

from unittest.mock import AsyncMock, patch

import pytest

from fastapi_agent.fastapi_discovery import FastAPIDiscovery, RouteInfo


class TestFastAPIDiscovery:
    """Test the FastAPIDiscovery class"""

    def test_discover_all_routes(self, app_no_auth):
        """Should discover all routes in the application"""
        discovery = FastAPIDiscovery(app_no_auth)

        # Should find at least our main routes
        paths = [route.path for route in discovery.routes_info]
        assert "/" in paths
        assert "/users" in paths
        assert "/users/{user_id}" in paths

    def test_discover_with_ignore_routes(self, app_no_auth):
        """Should filter out routes specified in ignore_routes"""
        discovery = FastAPIDiscovery(
            app_no_auth, ignore_routes=["GET:/users/{user_id}", "POST:/users"]
        )

        paths = [route.path for route in discovery.routes_info]
        methods_paths = [f"{route.method}:{route.path}" for route in discovery.routes_info]

        # Root should still be there
        assert "/" in paths

        # These should be ignored
        assert "GET:/users/{user_id}" not in methods_paths
        assert "POST:/users" not in methods_paths

        # GET /users should still be there (not ignored)
        assert any(r.path == "/users" and r.method == "GET" for r in discovery.routes_info)

    def test_discover_with_allow_routes(self, app_no_auth):
        """Should only include routes specified in allow_routes"""
        discovery = FastAPIDiscovery(app_no_auth, allow_routes=["GET:/users", "GET:/"])

        methods_paths = [f"{route.method}:{route.path}" for route in discovery.routes_info]

        # Should only have allowed routes
        assert "GET:/users" in methods_paths
        assert "GET:/" in methods_paths

        # Should not have other routes
        assert "GET:/users/{user_id}" not in methods_paths
        assert "POST:/users" not in methods_paths

    def test_extract_route_metadata(self, app_no_auth):
        """Should extract comprehensive metadata from routes"""
        discovery = FastAPIDiscovery(app_no_auth)

        # Find the /users/{user_id} route
        route = next(
            (r for r in discovery.routes_info if r.path == "/users/{user_id}"), None
        )
        assert route is not None

        # Check metadata
        assert route.method == "GET"
        assert route.name is not None
        assert "user" in route.description.lower() or route.description != ""
        assert route.response_model is not None

    def test_route_with_pydantic_models(self, app_no_auth):
        """Should extract Pydantic model schemas"""
        discovery = FastAPIDiscovery(app_no_auth)

        # Find POST /users route (has request body)
        route = next(
            (
                r
                for r in discovery.routes_info
                if r.path == "/users" and r.method == "POST"
            ),
            None,
        )
        assert route is not None

        # Should have request body schema
        assert route.request_body is not None
        assert isinstance(route.request_body, dict)

        # Should have response model schema
        assert route.response_model is not None
        assert isinstance(route.response_model, dict)

    def test_route_with_path_params(self, app_no_auth):
        """Should detect path parameters"""
        discovery = FastAPIDiscovery(app_no_auth)

        # Find route with path parameter
        route = next(
            (r for r in discovery.routes_info if r.path == "/users/{user_id}"), None
        )
        assert route is not None

        # Should have user_id parameter
        assert "user_id" in route.parameters
        assert route.parameters["user_id"]["required"] is True

    def test_get_routes_summary(self, app_no_auth):
        """Should generate human-readable route summary"""
        discovery = FastAPIDiscovery(app_no_auth)
        summary = discovery.get_routes_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

        # Should contain route information
        assert "GET /users" in summary
        assert "POST /users" in summary
        assert "users" in summary.lower()

    def test_get_openapi_spec(self, app_no_auth):
        """Should generate OpenAPI specification"""
        discovery = FastAPIDiscovery(app_no_auth)
        openapi_spec = discovery.get_openapi_spec()

        assert isinstance(openapi_spec, dict)
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert openapi_spec["info"]["title"] == "Test API"
        assert openapi_spec["info"]["version"] == "1.0.0"

        # paths should be removed per implementation
        assert "paths" not in openapi_spec

    @pytest.mark.asyncio
    async def test_execute_route_no_auth(self, app_no_auth, mock_httpx_client):
        """Should execute route without authentication"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        # Mock the httpx client
        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("GET", "/users")

        assert result["status_code"] == 200
        assert "data" in result
        assert "headers" in result

        # Verify client was called correctly
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_route_with_bearer_auth(
        self, app_bearer_auth, mock_httpx_client
    ):
        """Should execute route with Bearer authentication"""
        discovery = FastAPIDiscovery(
            app_bearer_auth,
            base_url="http://test:8000",
            auth={"Authorization": "Bearer valid_token"},
        )

        # Mock the httpx client
        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("GET", "/users")

        assert result["status_code"] == 200

        # Verify auth was passed in headers
        call_kwargs = mock_httpx_client.get.call_args[1]
        assert "headers" in call_kwargs
        # Auth should be in headers dict
        headers = call_kwargs["headers"]
        assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_execute_route_with_apikey_header(
        self, app_apikey_header, mock_httpx_client
    ):
        """Should execute route with API Key in header"""
        discovery = FastAPIDiscovery(
            app_apikey_header,
            base_url="http://test:8000",
            auth={"X-API-Key": "valid_api_key"},
        )

        # Mock the httpx client
        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("GET", "/users")

        assert result["status_code"] == 200

        # Verify API key was passed in headers
        call_kwargs = mock_httpx_client.get.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["X-API-Key"] == "valid_api_key"

    @pytest.mark.asyncio
    async def test_execute_route_post_with_data(self, app_no_auth, mock_httpx_client):
        """Should execute POST route with JSON data"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        user_data = {"name": "Charlie", "email": "charlie@example.com", "age": 35}

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("POST", "/users", data=user_data)

        assert result["status_code"] == 201

        # Verify data was passed correctly
        call_kwargs = mock_httpx_client.post.call_args[1]
        assert "json" in call_kwargs
        assert call_kwargs["json"] == user_data

    @pytest.mark.asyncio
    async def test_execute_route_with_query_params(
        self, app_no_auth, mock_httpx_client
    ):
        """Should execute route with query parameters"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route(
                "GET", "/users", limit=10, offset=0
            )

        assert result["status_code"] == 200

        # Verify params were passed correctly
        call_kwargs = mock_httpx_client.get.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"]["limit"] == 10
        assert call_kwargs["params"]["offset"] == 0

    @pytest.mark.asyncio
    async def test_execute_route_put_method(self, app_no_auth, mock_httpx_client):
        """Should execute PUT request"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        update_data = {"name": "Alice Updated"}

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route(
                "PUT", "/users/1", data=update_data
            )

        assert result["status_code"] == 200
        mock_httpx_client.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_route_delete_method(self, app_no_auth, mock_httpx_client):
        """Should execute DELETE request"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("DELETE", "/users/1")

        assert result["status_code"] == 200
        mock_httpx_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_route_patch_method(self, app_no_auth, mock_httpx_client):
        """Should execute PATCH request"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        patch_data = {"age": 31}

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route(
                "PATCH", "/users/1", data=patch_data
            )

        assert result["status_code"] == 200
        mock_httpx_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_route_unsupported_method(self, app_no_auth):
        """Should handle unsupported HTTP methods"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        result = await discovery.execute_route("INVALID", "/users")

        assert "error" in result
        assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_route_error_handling(self, app_no_auth, mock_httpx_client):
        """Should handle execution errors gracefully"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000")

        # Make the client raise an exception
        mock_httpx_client.get.side_effect = Exception("Connection error")

        with patch.object(discovery, "client", mock_httpx_client):
            result = await discovery.execute_route("GET", "/users")

        assert "error" in result
        assert "Connection error" in result["error"]

    def test_get_allow_methods(self, app_no_auth):
        """Should return list of HTTP methods used in routes"""
        discovery = FastAPIDiscovery(app_no_auth)
        methods = discovery.get_allow_methods()

        assert isinstance(methods, list)
        assert "GET" in methods
        assert "POST" in methods

    def test_get_routes_path(self, app_no_auth):
        """Should return list of route paths"""
        discovery = FastAPIDiscovery(app_no_auth)
        paths = discovery.get_routes_path()

        assert isinstance(paths, list)
        assert "/" in paths
        assert "/users" in paths

    def test_base_url_trailing_slash_removal(self, app_no_auth):
        """Should remove trailing slash from base_url"""
        discovery = FastAPIDiscovery(app_no_auth, base_url="http://test:8000/")

        assert discovery.base_url == "http://test:8000"

    @pytest.mark.asyncio
    async def test_close_client(self, app_no_auth):
        """Should close httpx client properly"""
        discovery = FastAPIDiscovery(app_no_auth)

        # Mock the client's aclose method
        discovery.client.aclose = AsyncMock()

        await discovery.close()

        discovery.client.aclose.assert_called_once()

    def test_route_info_model(self):
        """Should create RouteInfo model correctly"""
        route_info = RouteInfo(
            path="/test",
            method="GET",
            name="test_route",
            description="Test route description",
            parameters={"id": {"type": "int", "required": True}},
            request_body=None,
            response_model={"type": "object"},
            tags=["test"],
            dependencies=None,
        )

        assert route_info.path == "/test"
        assert route_info.method == "GET"
        assert route_info.name == "test_route"
        assert "id" in route_info.parameters
        assert route_info.tags == ["test"]

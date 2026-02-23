"""Tests for authentication detection in FastAPI Agent"""

import pytest

from fastapi_agent.fastapi_auth import (
    AuthConfig,
    AuthenticationDetector,
    AuthType,
    detect_auth,
)


class TestAuthenticationDetector:
    """Test the AuthenticationDetector class"""

    def test_detect_no_auth(self, app_no_auth):
        """Should detect when app has no authentication"""
        detector = AuthenticationDetector(app_no_auth)
        auth_config = detector.detected_auth

        assert auth_config.auth_type == AuthType.NONE
        assert auth_config.parameter_name == ""

    def test_detect_bearer_auth(self, app_bearer_auth):
        """Should detect HTTP Bearer authentication pattern"""
        detector = AuthenticationDetector(app_bearer_auth)
        auth_config = detector.detected_auth

        assert auth_config.auth_type == AuthType.HTTP_BEARER
        assert auth_config.parameter_name is not None
        assert auth_config.security_scheme is not None

    def test_detect_apikey_header(self, app_apikey_header):
        """Should detect API Key in header authentication"""
        detector = AuthenticationDetector(app_apikey_header)
        auth_config = detector.detected_auth

        assert auth_config.auth_type == AuthType.API_KEY_HEADER
        assert auth_config.header_name == "X-API-Key"
        assert auth_config.security_scheme is not None

    def test_detect_apikey_query(self, app_apikey_query):
        """Should detect API Key in query parameter authentication"""
        detector = AuthenticationDetector(app_apikey_query)
        auth_config = detector.detected_auth

        assert auth_config.auth_type == AuthType.API_KEY_QUERY
        assert auth_config.parameter_name is not None
        assert auth_config.security_scheme is not None

    def test_detect_basic_auth(self, app_basic_auth):
        """Should detect HTTP Basic authentication"""
        detector = AuthenticationDetector(app_basic_auth)
        auth_config = detector.detected_auth

        assert auth_config.auth_type == AuthType.HTTP_BASIC
        assert auth_config.security_scheme is not None

    def test_detect_multiple_auth_voting(self, app_multiple_auth):
        """Should use voting algorithm to select most common auth pattern"""
        detector = AuthenticationDetector(app_multiple_auth)
        auth_config = detector.detected_auth

        # Bearer is used on 3 routes, API Key on 1 route
        # So Bearer should win
        assert auth_config.auth_type == AuthType.HTTP_BEARER

    def test_auth_config_pattern_key(self):
        """Should generate correct pattern key for deduplication"""
        config = AuthConfig(
            auth_type=AuthType.API_KEY_HEADER,
            parameter_name="api_key",
            header_name="X-API-Key",
        )

        pattern_key = config.pattern_key
        assert pattern_key == (AuthType.API_KEY_HEADER, "X-API-Key")

    def test_auth_config_dedup_key(self):
        """Should generate correct dedup key"""

        def dummy_func():
            pass

        config = AuthConfig(
            auth_type=AuthType.API_KEY_HEADER,
            parameter_name="api_key",
            header_name="X-API-Key",
            dependency_function=dummy_func,
        )

        dedup_key = config.dedup_key
        assert dedup_key == (dummy_func, AuthType.API_KEY_HEADER, "X-API-Key", "api_key")

    def test_detect_auth_convenience_function(self, app_bearer_auth):
        """Should provide convenience function for quick detection"""
        auth_config = detect_auth(app_bearer_auth)

        assert isinstance(auth_config, AuthConfig)
        assert auth_config.auth_type == AuthType.HTTP_BEARER

    def test_get_analyzable_routes(self, app_bearer_auth):
        """Should filter out public routes from analysis"""
        detector = AuthenticationDetector(app_bearer_auth)
        routes = detector._get_analyzable_routes()

        # Should exclude /docs, /redoc, /openapi.json if present
        paths = [route.path for route in routes]
        assert "/docs" not in paths
        assert "/redoc" not in paths
        assert "/openapi.json" not in paths

    def test_auth_strength_ordering(self):
        """Should have correct strength ordering for tie-breaking"""
        detector = AuthenticationDetector.__dict__["AUTH_STRENGTH"]

        assert detector[AuthType.HTTP_BEARER] > detector[AuthType.API_KEY_HEADER]
        assert detector[AuthType.API_KEY_HEADER] > detector[AuthType.API_KEY_QUERY]
        assert detector[AuthType.API_KEY_QUERY] > detector[AuthType.HTTP_BASIC]
        assert detector[AuthType.HTTP_BASIC] > detector[AuthType.CUSTOM_HEADER]
        assert detector[AuthType.CUSTOM_HEADER] > detector[AuthType.NONE]

    def test_analyze_route_auth(self, app_bearer_auth):
        """Should analyze individual route auth dependencies"""
        detector = AuthenticationDetector(app_bearer_auth)

        # Get the /users route
        routes = [route for route in app_bearer_auth.routes if route.path == "/users"]
        assert len(routes) > 0

        route = routes[0]
        route_auth_config = detector._analyze_route_auth(route)

        assert route_auth_config is not None
        assert route_auth_config.has_auth is True
        assert route_auth_config.primary_auth is not None
        assert route_auth_config.primary_auth.auth_type == AuthType.HTTP_BEARER

    def test_deduplicate_auth_configs(self):
        """Should remove duplicate auth configurations"""

        def dummy_func():
            pass

        config1 = AuthConfig(
            auth_type=AuthType.HTTP_BEARER,
            parameter_name="token",
            dependency_function=dummy_func,
        )

        # Same config (should be deduplicated)
        config2 = AuthConfig(
            auth_type=AuthType.HTTP_BEARER,
            parameter_name="token",
            dependency_function=dummy_func,
        )

        # Different config
        config3 = AuthConfig(
            auth_type=AuthType.API_KEY_HEADER,
            parameter_name="key",
            header_name="X-API-Key",
            dependency_function=dummy_func,
        )

        detector = AuthenticationDetector.__new__(AuthenticationDetector)
        unique_configs = detector._deduplicate_auth_configs([config1, config2, config3])

        assert len(unique_configs) == 2
        assert config1 in unique_configs or config2 in unique_configs
        assert config3 in unique_configs

    def test_route_auth_config_properties(self):
        """Should provide useful properties on RouteAuthConfig"""
        from fastapi_agent.fastapi_auth import RouteAuthConfig

        config1 = AuthConfig(
            auth_type=AuthType.HTTP_BEARER,
            parameter_name="token",
        )

        config2 = AuthConfig(
            auth_type=AuthType.API_KEY_HEADER,
            parameter_name="key",
            header_name="X-API-Key",
        )

        route_config = RouteAuthConfig(auth_dependencies=[config1, config2])

        assert route_config.has_auth is True
        assert route_config.primary_auth == config1
        assert len(route_config.get_auth_by_type(AuthType.HTTP_BEARER)) == 1
        assert len(route_config.get_auth_by_type(AuthType.API_KEY_HEADER)) == 1
        assert len(route_config.get_auth_by_type(AuthType.NONE)) == 0

    def test_route_auth_config_no_auth(self):
        """Should handle RouteAuthConfig with no auth dependencies"""
        from fastapi_agent.fastapi_auth import RouteAuthConfig

        route_config = RouteAuthConfig(auth_dependencies=[])

        assert route_config.has_auth is False
        assert route_config.primary_auth is None

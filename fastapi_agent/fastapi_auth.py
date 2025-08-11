import inspect
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional, Set, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPBasic, HTTPBearer


class AuthType(Enum):
    """Supported authentication types"""

    NONE = "none"
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    HTTP_BEARER = "http_bearer"
    HTTP_BASIC = "http_basic"
    CUSTOM_HEADER = "custom_header"


@dataclass(frozen=True)
class AuthConfig:
    """Configuration for detected authentication"""

    auth_type: AuthType
    parameter_name: str
    security_scheme: Optional[Any] = None
    dependency_function: Optional[Callable] = None
    header_name: Optional[str] = None

    @property
    def pattern_key(self) -> Tuple[AuthType, str]:
        """Unique key for deduplication"""
        name = self.header_name or self.parameter_name or ""
        return (self.auth_type, name)

    @property
    def dedup_key(self) -> Tuple[Callable, AuthType, Optional[str], str]:
        """Key for removing duplicate configs within a route"""
        return (
            self.dependency_function,
            self.auth_type,
            self.header_name,
            self.parameter_name,
        )


@dataclass
class RouteAuthConfig:
    """Configuration for all authentication dependencies on a route"""

    auth_dependencies: List[AuthConfig] = field(default_factory=list)

    @property
    def has_auth(self) -> bool:
        return len(self.auth_dependencies) > 0

    @property
    def primary_auth(self) -> Optional[AuthConfig]:
        """Get the primary (first) authentication dependency"""
        return self.auth_dependencies[0] if self.auth_dependencies else None

    def get_auth_by_type(self, auth_type: AuthType) -> List[AuthConfig]:
        """Get all auth dependencies of a specific type"""
        return [auth for auth in self.auth_dependencies if auth.auth_type == auth_type]


class AuthenticationDetector:
    """Detects authentication patterns in FastAPI applications"""

    # Routes to ignore when detecting authentication patterns
    PUBLIC_ROUTES = {"/docs", "/redoc", "/openapi.json"}

    # Authentication strength for tie-breaking
    AUTH_STRENGTH = {
        AuthType.HTTP_BEARER: 4,
        AuthType.API_KEY_HEADER: 3,
        AuthType.API_KEY_QUERY: 2,
        AuthType.HTTP_BASIC: 1,
        AuthType.CUSTOM_HEADER: 0,
        AuthType.NONE: -1,
    }

    def __init__(self, app: FastAPI):
        self.app = app
        self._detected_auth: Optional[AuthConfig] = None

    @property
    def detected_auth(self) -> AuthConfig:
        """Get the detected authentication config, computing it if needed"""
        if self._detected_auth is None:
            self._detected_auth = self._detect_primary_auth_pattern()
        return self._detected_auth

    def _detect_primary_auth_pattern(self) -> AuthConfig:
        """Determine the most common auth pattern across the app's routes"""
        pattern_counts: Counter[Tuple[AuthType, str]] = Counter()
        pattern_examples: dict[Tuple[AuthType, str], AuthConfig] = {}

        for route in self._get_analyzable_routes():
            route_auth = self._analyze_route_auth(route)
            if not route_auth:
                continue

            # Track each unique pattern once per route
            seen_patterns: Set[Tuple[AuthType, str]] = set()
            for auth_config in route_auth.auth_dependencies:
                pattern_key = auth_config.pattern_key

                if pattern_key not in seen_patterns:
                    seen_patterns.add(pattern_key)
                    pattern_counts[pattern_key] += 1
                    pattern_examples.setdefault(pattern_key, auth_config)

        if not pattern_counts:
            return AuthConfig(AuthType.NONE, "")

        return self._select_best_pattern(pattern_counts, pattern_examples)

    def _get_analyzable_routes(self) -> List[APIRoute]:
        """Get routes that should be analyzed for authentication"""
        return [
            route
            for route in self.app.routes
            if isinstance(route, APIRoute) and route.path not in self.PUBLIC_ROUTES
        ]

    def _select_best_pattern(
        self,
        pattern_counts: Counter[Tuple[AuthType, str]],
        pattern_examples: dict[Tuple[AuthType, str], AuthConfig],
    ) -> AuthConfig:
        """Select the best authentication pattern from candidates"""
        # Get all patterns with the highest count
        max_count = pattern_counts.most_common(1)[0][1]
        top_patterns = [
            pattern for pattern, count in pattern_counts.items() if count == max_count
        ]

        # Sort by strength (descending) then by name (ascending) for deterministic results
        best_pattern = min(
            top_patterns, key=lambda p: (-self.AUTH_STRENGTH[p[0]], p[1])
        )

        return pattern_examples[best_pattern]

    def _analyze_route_auth(self, route: APIRoute) -> Optional[RouteAuthConfig]:
        """Analyze a single route to detect all its authentication methods"""
        auth_configs: List[AuthConfig] = []

        # Analyze route-level dependencies
        if hasattr(route, "dependencies") and route.dependencies:
            for dep in route.dependencies:
                auth_configs.extend(self._analyze_dependency(dep.dependency))

        # Analyze endpoint dependencies from dependant graph
        if (
            hasattr(route, "dependant")
            and route.dependant
            and hasattr(route.dependant, "dependencies")
            and route.dependant.dependencies
        ):
            for depend in route.dependant.dependencies:
                auth_configs.extend(self._analyze_dependency(depend.call))

        # Analyze function signature dependencies
        if route.endpoint:
            auth_configs.extend(self._analyze_endpoint_signature(route.endpoint))

        if not auth_configs:
            return None

        # Remove duplicates
        unique_configs = self._deduplicate_auth_configs(auth_configs)
        return RouteAuthConfig(auth_dependencies=unique_configs)

    def _analyze_endpoint_signature(self, endpoint: Callable) -> List[AuthConfig]:
        """Analyze endpoint function signature for authentication dependencies"""
        auth_configs: List[AuthConfig] = []

        try:
            sig = inspect.signature(endpoint)
            for param in sig.parameters.values():
                if param.default != inspect.Parameter.empty and hasattr(
                    param.default, "dependency"
                ):
                    auth_configs.extend(
                        self._analyze_dependency(param.default.dependency)
                    )
        except Exception as e:
            print(f"Error analyzing endpoint signature {endpoint}: {e}")

        return auth_configs

    def _deduplicate_auth_configs(self, configs: List[AuthConfig]) -> List[AuthConfig]:
        """Remove duplicate auth configurations"""
        seen: Set[Tuple[Callable, AuthType, Optional[str], str]] = set()
        unique_configs: List[AuthConfig] = []

        for config in configs:
            if config.dedup_key not in seen:
                seen.add(config.dedup_key)
                unique_configs.append(config)

        return unique_configs

    def _analyze_dependency(self, dependency_func: Callable) -> List[AuthConfig]:
        """Analyze a dependency function to determine ALL auth types it declares"""
        if not callable(dependency_func):
            return []

        auth_configs: List[AuthConfig] = []

        try:
            sig = inspect.signature(dependency_func)
            for param_name, param in sig.parameters.items():
                # Skip variadic parameters
                if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    continue

                config = self._analyze_parameter(param, param_name, dependency_func)
                if config:
                    auth_configs.append(config)

        except Exception as e:
            print(f"Error analyzing dependency {dependency_func}: {e}")

        return auth_configs

    def _analyze_parameter(
        self, param: inspect.Parameter, param_name: str, dependency_func: Callable
    ) -> Optional[AuthConfig]:
        """Analyze a single parameter for authentication configuration"""
        param_default = param.default if param.default != param.empty else None

        # Extract actual dependency from Depends wrapper
        actual_dependency = getattr(param_default, "dependency", param_default)

        # Check for FastAPI security schemes
        config = self._check_security_schemes(
            param, param_name, actual_dependency, dependency_func
        )
        if config:
            return config

        # Check for custom header patterns
        return self._check_header_patterns(
            param, param_name, param_default, dependency_func
        )

    def _check_security_schemes(
        self,
        param: inspect.Parameter,
        param_name: str,
        actual_dependency: Any,
        dependency_func: Callable,
    ) -> Optional[AuthConfig]:
        """Check for FastAPI security scheme patterns"""
        param_annotation = (
            str(param.annotation) if param.annotation != param.empty else ""
        )

        # HTTP Bearer
        if "HTTPAuthorizationCredentials" in param_annotation and isinstance(
            actual_dependency, HTTPBearer
        ):
            return AuthConfig(
                auth_type=AuthType.HTTP_BEARER,
                parameter_name=param_name,
                security_scheme=actual_dependency,
                dependency_function=dependency_func,
            )

        # API Key Header
        if isinstance(actual_dependency, APIKeyHeader):
            return AuthConfig(
                auth_type=AuthType.API_KEY_HEADER,
                parameter_name=param_name,
                security_scheme=actual_dependency,
                header_name=getattr(actual_dependency.model, "name", None),
                dependency_function=dependency_func,
            )

        # API Key Query
        if isinstance(actual_dependency, APIKeyQuery):
            return AuthConfig(
                auth_type=AuthType.API_KEY_QUERY,
                parameter_name=param_name,
                security_scheme=actual_dependency,
                dependency_function=dependency_func,
            )

        # HTTP Basic
        if isinstance(actual_dependency, HTTPBasic):
            return AuthConfig(
                auth_type=AuthType.HTTP_BASIC,
                parameter_name=param_name,
                security_scheme=actual_dependency,
                dependency_function=dependency_func,
            )

        return None

    def _check_header_patterns(
        self,
        param: inspect.Parameter,
        param_name: str,
        param_default: Any,
        dependency_func: Callable,
    ) -> Optional[AuthConfig]:
        """Check for custom header patterns"""
        # Direct Header(...) parameter
        if param_default is not None and param_default.__class__.__name__ == "Header":
            header_name = self._extract_header_name(param_default, param_name)
            return AuthConfig(
                auth_type=AuthType.CUSTOM_HEADER,
                parameter_name=param_name,
                header_name=header_name,
                dependency_function=dependency_func,
            )

        # Depends(Header(...)) pattern
        if hasattr(param_default, "dependency") and "Header" in str(
            param_default.dependency
        ):
            header_name = self._extract_header_from_depends(param_default, param_name)
            if header_name:
                return AuthConfig(
                    auth_type=AuthType.CUSTOM_HEADER,
                    parameter_name=param_name,
                    header_name=header_name,
                    dependency_function=dependency_func,
                )

        # Fallback Header pattern
        if param_default and "Header" in str(param_default):
            header_name = self._extract_header_name(param_default, param_name)
            return AuthConfig(
                auth_type=AuthType.CUSTOM_HEADER,
                parameter_name=param_name,
                header_name=header_name,
                dependency_function=dependency_func,
            )

        return None

    def _extract_header_name(self, header_obj: Any, param_name: str) -> str:
        """Extract header name from Header object with intelligent fallback"""
        # Try to get explicit alias
        if hasattr(header_obj, "alias") and header_obj.alias:
            return header_obj.alias

        # Try to get name attribute
        if hasattr(header_obj, "name") and header_obj.name:
            return header_obj.name

        # Convert parameter name to proper header format
        return self._param_name_to_header(param_name)

    def _extract_header_from_depends(self, depends_obj: Any, param_name: str) -> str:
        """Extract header name from Depends(Header()) object"""
        if not hasattr(depends_obj, "dependency"):
            return self._param_name_to_header(param_name)

        header_func = depends_obj.dependency
        if hasattr(header_func, "alias") and header_func.alias:
            return header_func.alias

        return self._param_name_to_header(param_name)

    def _param_name_to_header(self, param_name: str) -> str:
        """Convert parameter name to proper HTTP header format"""
        # Convert snake_case to Title-Case
        return "-".join(word.capitalize() for word in param_name.split("_"))


# Convenience function for quick detection
def detect_auth(app: FastAPI) -> AuthConfig:
    """Detect the primary authentication pattern in a FastAPI app"""
    detector = AuthenticationDetector(app)
    return detector.detected_auth

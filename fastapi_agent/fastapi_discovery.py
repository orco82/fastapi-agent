import inspect
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel


class RouteInfo(BaseModel):
    """Information about a FastAPI route"""

    path: str
    method: str
    name: str
    description: str
    parameters: Dict[str, Any]
    request_body: Optional[Dict[str, Any]]
    response_model: Optional[Dict[str, Any]]
    tags: List[str]
    headers: Optional[Union[Dict[str, Any], List]] = None


class FastAPIDiscovery:
    """
    Discovery routes, sechmas, and other information from FastAPI application

    Args:
        app (FastAPI): The FastAPI application instance to extract route information from.
        base_url (str): The base URL of the FastAPI application for documentation and interaction.
                        Defaults to "http://localhost:8000".
        deps (Optional[dict]): Optional dictionary of dependencies or external components relevant to the API.
                                Support for API with token keys passed in the Headers.
        ignore_routes (Optional[list]): List of route paths to ignore when building the route prompt context.
    """
    def __init__(
        self,
        app: FastAPI,
        base_url: str = "http://localhost:8000",
        deps: Optional[dict] = None,
        ignore_routes: Optional[list] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.app = app
        self.base_url = base_url.rstrip("/")
        self.deps = deps
        self.header_deps = {}
        self.ignore_routes = ignore_routes or []

        if logger is None:
            logger = logging.getLogger(__name__)
            logger.addHandler(logging.NullHandler())
        self.logger = logger

        self.routes_info: List[RouteInfo] = []
        self.client = httpx.AsyncClient(verify=False)
        self._discover_routes()

    def _discover_routes(self):
        """Discover all routes in the FastAPI app"""
        self.routes_info = []

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                if route.path in self.ignore_routes:
                    continue

                route_info = self._extract_route_info(route)
                if route_info:
                    self.routes_info.append(route_info)

                if self.deps:
                    for deps in self.deps:
                        if re.sub(r"[-_]", " ", deps) in [
                            re.sub(r"[-_]", " ", d.name) for d in route_info.headers
                        ]:
                            self.header_deps.update({deps: self.deps[deps]})
                        # TODO: add support for other depends like qurey

    def _extract_route_info(self, route: APIRoute) -> Optional[RouteInfo]:
        """Extract detailed information from a FastAPI route"""
        try:
            # Get the endpoint function
            endpoint = route.endpoint

            # Extract docstring as description
            description = endpoint.__doc__ or "No description available"
            description = " ".join(description.split())  # Clean up whitespace

            # Get parameters from function signature
            sig = inspect.signature(endpoint)
            parameters = {}
            request_body = None

            headers = []
            for depend in route.dependant.dependencies:
                for header in depend.header_params:
                    headers.append(header)

            for param_name, param in sig.parameters.items():
                if param_name in ["request", "response"]:
                    continue

                if "BackgroundTasks" in str(param.annotation):
                    continue

                # check if param is not Depends and not in the header_params
                if not (
                    "Depends" in str(param.default)
                    and param_name in [h.name for h in headers]
                ):
                    param_info = {
                        "type": str(param.annotation)
                        if param.annotation != param.empty
                        else "Any",
                        "required": param.default == param.empty,
                        "default": str(param.default)
                        if param.default != param.empty
                        else None,
                    }

                    # Check if this is a request body (Pydantic model)
                    if (
                        param.annotation != param.empty
                        and hasattr(param.annotation, "__bases__")
                        and BaseModel in param.annotation.__bases__
                    ):
                        request_body = self._get_pydantic_schema(param.annotation)
                    else:
                        parameters[param_name] = param_info

            # Get response model info
            response_model = None
            if route.response_model:
                response_model = self._get_pydantic_schema(route.response_model)

            return RouteInfo(
                path=route.path,
                method=list(route.methods)[0],  # Get first method
                name=route.name,
                description=description,
                parameters=parameters,
                request_body=request_body,
                response_model=response_model,
                tags=route.tags or [],
                headers=headers,
            )
        except Exception as e:
            self.logger.error(f"failed extracting route info for {route.path}: {e}")
            return None

    def _get_pydantic_schema(self, model_class) -> Dict[str, Any]:
        """Get schema information from a Pydantic model"""
        try:
            if hasattr(model_class, "model_json_schema"):
                return model_class.model_json_schema()
            elif hasattr(model_class, "schema"):
                return model_class.schema()
            else:
                return {"type": str(model_class)}
        except:  # noqa: E722
            return {"type": str(model_class)}

    def get_allow_methods(self) -> list:
        methods = []
        for r in self.routes_info:
            methods.append(r.method)
        return list(set(methods))

    def get_routes_path(self) -> list:
        return [r.path for r in self.app.router.routes]

    def get_routes_summary(self) -> str:
        """Get a human-readable summary of all routes for LLM context"""
        summary = ""

        for route in self.routes_info:
            summary += f"**{route.method.upper()} {route.path}**\n"
            summary += f"Name: {route.name}\n"
            summary += f"Description: {route.description}\n"

            if route.parameters:
                summary += "Parameters:\n"
                for param_name, param_info in route.parameters.items():
                    required = "required" if param_info["required"] else "optional"
                    summary += f"  - {param_name} ({param_info['type']}) - {required}\n"

            if route.request_body:
                summary += f"Request Body: {json.dumps(route.request_body, indent=2)}\n"

            if route.response_model:
                summary += (
                    f"Response Model: {json.dumps(route.response_model, indent=2)}\n"
                )

            if route.headers:
                summary += f"Hadears: {route.headers}\n"

            if route.tags:
                summary += f"Tags: {', '.join(route.tags)}\n"

            summary += "\n" + "-" * 50 + "\n"

        return summary

    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get the OpenAPI specification"""
        openapi_spec = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
        del openapi_spec["paths"]
        return openapi_spec

    async def execute_route(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute a route with given parameters"""
        url = f"{self.base_url}{path}"
        headers_data = kwargs.pop("header", {})
        headers_data.update(self.header_deps)
        json_data = kwargs.pop("data", None)

        self.logger.debug(f" URL: {url}")
        self.logger.debug(f" Method: {method}")
        self.logger.debug(f" Header Deps: {self.header_deps}")
        self.logger.debug(f" Headers: {headers_data}")
        self.logger.debug(f" Data: {json_data}")
        self.logger.debug(f" Params: {kwargs}")

        try:
            if method.upper() == "GET":
                response = await self.client.get(
                    url, headers=headers_data, params=kwargs
                )
            elif method.upper() == "POST":
                response = await self.client.post(
                    url, json=json_data, headers=headers_data, params=kwargs
                )
            elif method.upper() == "PUT":
                response = await self.client.put(
                    url, json=json_data, headers=headers_data, params=kwargs
                )
            elif method.upper() == "DELETE":
                response = await self.client.delete(
                    url, headers=headers_data, params=kwargs
                )
            elif method.upper() == "PATCH":
                response = await self.client.patch(
                    url, headers=headers_data, params=kwargs
                )
            else:
                self.logger.error(f"Method {method} not supported")
                return {"error": f"Method {method} not supported"}

            self.logger.info(f"execute route {method} {url} - {response.status_code}")
            return {
                "status_code": response.status_code,
                "data": response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else response.text,
                "headers": dict(response.headers),
            }
        except Exception as e:
            self.logger.error(f"Fail execute route - {e}")
            return {"error": str(e)}

    def get_route_usage_example(self, route: RouteInfo) -> str:
        """Generate usage example for a route"""
        example = f"# {route.method.upper()} {route.path}\n"
        example += f"# {route.description}\n\n"

        if route.method.upper() == "GET":
            params = []
            if route.parameters:
                for param_name, param_info in route.parameters.items():
                    if param_info["required"]:
                        params.append(f"{param_name}='value'")
                    else:
                        params.append(f"{param_name}='optional_value'")

            example += f"await agent.execute_route('{route.method}', '{route.path}'"
            if params:
                example += f", {', '.join(params)}"
            if route.headers:
                example += f", header={{{route.headers[0].name}: 'value'}}"
            example += ")\n"

        elif route.method.upper() in ["POST", "PUT"]:
            example += f"await agent.execute_route('{route.method}', '{route.path}'"
            if route.request_body:
                example += ", data={'key': 'value'}"
            if route.headers:
                example += f", header={{{route.headers[0].name}: 'value'}}"
            example += ")\n"

        return example

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

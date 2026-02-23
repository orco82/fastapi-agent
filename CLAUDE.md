# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI Agent is a Python library that integrates AI capabilities into FastAPI applications, enabling natural language interaction with API endpoints through an LLM-powered agent. The library automatically discovers routes, detects authentication patterns, and provides both API and web-based chat interfaces.

## Development Commands

### Environment Setup
```bash
# Create virtual environment (Python 3.13)
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -e .

# Using uv (alternative)
uv sync
```

### Building and Publishing
```bash
# Complete build and publish workflow (from _update_pkg.txt)
# Clean previous builds and cache
rm -rf dist/ .venv/
uv cache clean

# Sync dependencies
uv sync

# Install build tools
uv pip install twine==6.0.1 hatchling pip

# Build package
uv build

# Verify built package
uv run twine check dist/*

# Upload to PyPI (requires credentials)
uv run twine upload dist/*
```

### Code Quality
```bash
# Lint with ruff (configured in pyproject.toml)
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Running Tests
```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage report
pytest --cov=fastapi_agent --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_detect_bearer_auth

# Run tests in verbose mode
pytest -v

# Generate HTML coverage report
pytest --cov=fastapi_agent --cov-report=html
# Open htmlcov/index.html in browser
```

### Running Examples
```bash
# Run FastAPI examples (requires OPENAI_API_KEY in .env)
cd examples
python 1_ai_agent_example.py          # Standalone AI agent with custom tools
python 2_fastapi_discovery_example.py # Route discovery only
python 3_fastapi_agent_example.py     # Full FastAPI integration with chat UI
python fastapi_app.py                 # Complete app with authentication
```

## Architecture Overview

### Component Hierarchy (Inheritance Chain)

```
AuthenticationDetector (fastapi_auth.py)
        ↓
FastAPIDiscovery (fastapi_discovery.py)
        ↓
FastAPIAgent (fastapi_agent.py)
```

### Core Components

**1. AuthenticationDetector (`fastapi_auth.py`)**
- Scans FastAPI routes to automatically detect authentication mechanisms
- Supports: HTTP Bearer, API Key (header/query), HTTP Basic, Custom Headers
- Uses voting algorithm to determine primary auth pattern based on frequency
- Key class: `AuthenticationDetector` with `detect_authentication()` method

**2. FastAPIDiscovery (`fastapi_discovery.py`)**
- Inherits from `AuthenticationDetector`
- Discovers all routes and extracts comprehensive metadata (path, method, params, models)
- Filters routes via `ignore_routes` / `allow_routes` configuration
- Executes HTTP requests to routes via `httpx.AsyncClient` with auth injection
- Key method: `execute_route()` for calling API endpoints with proper authentication

**3. FastAPIAgent (`fastapi_agent.py`)**
- Inherits from `FastAPIDiscovery`
- Main integration layer that orchestrates everything
- Generates system prompts with full API context for the LLM
- Registers `api_request` tool enabling agent to call API endpoints
- Provides default routes: `/agent/query` (API) and `/agent/chat` (Web UI)
- Key method: `chat()` for processing user queries

**4. Agent Abstraction (`agents/`)**
- `base_agent.py`: Abstract base class defining agent interface
- `pydantic_ai.py`: Concrete implementation using Pydantic AI framework
- `__init__.py`: Factory pattern via `AIAgent.create()` for provider-agnostic instantiation
- Designed to be extensible (can add LangChain, CrewAI, etc.)

**5. Chat UI (`chat_ui/`)**
- HTML/CSS/JS for web-based chat interface served at `/agent/chat`
- Minimal, self-contained frontend

### Request Flow

```
User Query → /agent/query
      ↓
FastAPIAgent.chat()
      ↓
PydanticAIAgent processes with system prompt (includes API docs)
      ↓
Agent decides which endpoint to call
      ↓
Invokes api_request tool
      ↓
FastAPIDiscovery.execute_route()
  - Injects auth based on detected type
  - Makes HTTP request via httpx
      ↓
Returns APIResponse
      ↓
Agent formulates natural language response
```

## Key Files and Locations

- **`fastapi_agent/__init__.py:1`**: Version definition (`__version__`)
- **`fastapi_agent/fastapi_agent.py:50`**: `FastAPIAgent.__init__()` - Main initialization
- **`fastapi_agent/fastapi_discovery.py:150`**: `execute_route()` - Route execution with auth
- **`fastapi_agent/fastapi_auth.py:100`**: `detect_authentication()` - Auth pattern detection
- **`fastapi_agent/agents/__init__.py:40`**: `AIAgent.create()` - Agent factory
- **`examples/`**: Working examples demonstrating different usage patterns

## Important Configuration

### Authentication Handling
When routes use FastAPI dependency injection for auth (e.g., `Depends(api_key_header)`), pass auth credentials to `FastAPIAgent`:

```python
FastAPIAgent(
    app,
    auth={"api-key": "xxx"}  # For header-based auth
    # OR
    auth={"Authorization": "Bearer xxx"}  # For Bearer tokens
)
```

The agent automatically detects the auth type and injects credentials when calling routes.

### Route Filtering
Control which routes the agent can access:

```python
FastAPIAgent(
    app,
    ignore_routes=["DELETE:/users/{user_id}"],  # Exclude specific routes
    # OR
    allow_routes=["GET:/users", "POST:/users"]   # Whitelist only these routes
)
```

Format: `["METHOD:/path"]`

## Dependencies

Core dependencies (from `pyproject.toml`):
- `fastapi>=0.116.1` - Web framework
- `httpx>=0.28.1` - HTTP client for route execution
- `pydantic>=2.11.7` - Data validation
- `pydantic-ai>=0.4.7` - AI agent framework
- `uvicorn>=0.35.0` - ASGI server

## Development Notes

### Ruff Configuration
The project uses Ruff for linting with specific rules (see `pyproject.toml:47-60`):
- Enabled: pycodestyle (E/W), pyflakes (F), comprehensions (C), bugbear (B)
- Ignored: E501 (line length), C901 (complexity), B904 (raise without from), B008 (function calls in defaults)

### Version Management
Version is defined in `fastapi_agent/__init__.py` and managed by Hatchling (see `pyproject.toml:44-45`).

### Testing
The project uses pytest with async support. All external dependencies (LLM calls, HTTP requests) are mocked for fast, reliable tests. Test fixtures are defined in `tests/conftest.py`.

Coverage goals:
- Authentication detection: 100% (critical security component)
- Route discovery: 90%+
- Agent orchestration: 85%+
- Overall: 80%+

Test files:
- `tests/test_auth.py` - Authentication detection tests
- `tests/test_discovery.py` - Route discovery tests
- `tests/test_agent.py` - FastAPI agent orchestration tests
- `tests/test_agents_factory.py` - Agent factory tests

### Python Version
Project targets Python 3.10+ (specified in `pyproject.toml:11`). Development uses Python 3.13 (`.python-version`).

## Common Patterns

### Adding a New Agent Provider
1. Create new file in `fastapi_agent/agents/` (e.g., `langchain_agent.py`)
2. Implement `BaseAgent` abstract class
3. Register in `agents/__init__.py` factory
4. Update `AIAgent.create()` to support new provider

### Extending Authentication Support
1. Add new `AuthType` enum value in `fastapi_auth.py`
2. Update `_analyze_dependency()` method to detect new auth pattern
3. Update `_format_auth_for_request()` in `fastapi_discovery.py` to inject new auth type

### Adding Custom Tools to Agent
Use `add_custom_tool()` method on agent instance:

```python
agent = AIAgent.create(model="openai:gpt-4.1-mini")
agent.add_custom_tool(my_custom_function)
```

See `examples/pydantic_ai_tools.py` for tool examples.

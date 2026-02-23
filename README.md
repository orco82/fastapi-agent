<p align="center">
  <!-- GitHub metrics -->

  <a href="https://github.com/orco82/fastapi-agent">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/orco82/fastapi-agent?style=for-the-badge&logo=github">
  </a>
  <a href="https://github.com/orco82/fastapi-agent/network/members">
    <img alt="GitHub forks" src="https://img.shields.io/github/forks/orco82/fastapi-agent?style=for-the-badge">
  </a>
  <a href="https://github.com/orco82/fastapi-agent/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/orco82/fastapi-agent?style=for-the-badge">
  </a>
  <a href="https://github.com/orco82/fastapi-agent/blob/main/LICENSE">
    <img alt="GitHub license" src="https://img.shields.io/github/license/orco82/fastapi-agent?style=for-the-badge">
  </a>
  <a href="https://github.com/orco82/fastapi-agent/commits/main">
    <img alt="Last commit" src="https://img.shields.io/github/last-commit/orco82/fastapi-agent?style=for-the-badge">
  </a>
  
  
  <!-- PyPI metrics -->
  
  <a href="https://pypi.org/project/fastapi-agent/">
    <img alt="PyPI version" src="https://img.shields.io/pypi/v/fastapi-agent?style=for-the-badge&logo=pypi">
  </a>
  <a href="https://pypi.org/project/fastapi-agent/">
    <img alt="PyPI downloads" src="https://img.shields.io/pypi/dm/fastapi-agent?style=for-the-badge">
  </a>
  
</p>

<div align="center">

![FastAPI Agent Logo](https://raw.githubusercontent.com/orco82/fastapi-agent/main/assets/fastapi-agent-1.png)

</div>

---

<p align="center" style="padding:10px;font-size:16px"> 💬 Talk to your FastAPI app like it's a teammate.</p>

<br>

FastAPI Agent integrates an AI Agent into your FastAPI application.<br>
It allows you to interact with your API endpoints through a chat interface or directly via an API route using an LLM (Large Language Model).

![fastapi screenshot](https://raw.githubusercontent.com/orco82/fastapi-agent/main/assets/fastapi-agent-screenshot.png)

## ⚙️ Installation:

To install the package, run:
```bash
# install with pip
pip install fastapi_agent

# install with uv
uv add fastapi_agent
```


## 🧪 Usage:

To use the FastAPI Agent, initialize it with your FastAPI app and AI model.<br>
You can use the default agent routes or add custom ones to your FastAPI application to interact with the agent via a chat interface or API endpoint.

Here is a simple example of how to use the FastAPI Agent with your FastAPI application:

#### .env
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### app.py
```python
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi_agent import FastAPIAgent

# load OPENAI_API_KEY from .env
load_dotenv()

# set your FastAPI app
app = FastAPI(
    title="YOUR APP TITLE",
    version="0.1.0",
    description="SOME DESCRIPTION",
)

# add routes
@app.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to Test API"}

# add the FastAPI Agent + default routes
FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
    base_url="http://localhost:8000",
    include_router=True,
)

# run FastAPI
uvicorn.run(app, host="0.0.0.0", port=8000)
```


## 🧭 Default Routes

FastAPI Agent provides two default routes:

1. **`/agent/query`** – Ask anything about your API using natural language. 🧠

  ```bash
curl -k -X POST "http://127.0.0.1:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "show all endpoints"}'
```

2. **`/agent/chat`** – A simple web-based chat interface to interact with your API. 💬

#### 💡 You can also add custom routes using agent.chat() method - [Example](https://github.com/orco82/fastapi-agent/blob/main/examples/3_fastapi_agent_example.py)
 

## 💬 AI Chat - Web UI
When you integrate **FastAPI Agent** into your FastAPI application, it automatically adds a new endpoint at `/agent/chat`, which provides a minimal chat interface to interact with your API.

![fastapi demo](https://raw.githubusercontent.com/orco82/fastapi-agent/main/assets/fastapi-agent-demo.gif)


## 🧩 Additional Arguments:

If your application routes use **Authorizations Depends** (e.g. Headers or Query String API key or HTTP_Bearer), you need to pass a dictionary of the authorizations.<br>
The agent will use them to call your routes and also apply authorizations dependencies to `/agent/query` route. (see [Additional Examples](https://github.com/orco82/fastapi-agent/blob/main/README.md#-additional-examples))

```python
api_key = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
    base_url="https://localhost:8000",
    auth={"api-key": API_KEY} || {'Authorization': "Bearer API_KEY"},
    include_router=True,
)
```

---

You can control which routes the agent can access using the `ignore_routes` or `allow_routes` arguments:
 - Use `ignore_routes` to exclude specific routes from being accessible to the agent.
 - Use `allow_routes` to restrict the agent to only the specified routes.

> Both `ignore_routes` and `allow_routes` must be a list of strings in the format: ["METHOD:/path"]

```python
FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
    base_url="https://localhost:8000",
    ignore_routes=["DELETE:/users/{user_id}"],
    include_router=True,
)
```


## 📁 Additional Examples:

Check out our examples for [ai_agent](https://github.com/orco82/fastapi-agent/blob/main/examples/1_ai_agent_example.py), 
[fastapi_discovery](https://github.com/orco82/fastapi-agent/blob/main/examples/2_fastapi_discovery_example.py), 
and [fastapi_agent](https://github.com/orco82/fastapi-agent/blob/main/examples/3_fastapi_agent_example.py).  
All examples are available [here](https://github.com/orco82/fastapi-agent/blob/main/examples/).

---

#### If you're using *Authorizations Depends* in your routes, make sure to pass the required headers when calling the `/agent/query` endpoint like in the examples below:

#### python
```python
import requests

res = requests.post(
    "http://127.0.0.1:8000/agent/query", 
    json={"query": "show all endpoints"},
    headers={"auth": '{"api-key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}'}
    - OR - 
    headers={"auth": '{"Authorization": "Bearer 12345678"}'}
)
print(res.json())
```

#### curl
```bash
curl -k -X POST "http://127.0.0.1:8000/agent/query" \
  -H 'auth: {"api-key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}' \
  - OR -
  -H 'auth: {"Authorization": "Bearer 12345678"}' \
  -H "Content-Type: application/json" \
  -d '{"query": "show all endpoints"}'
```


## 🧪 Development & Testing

FastAPI Agent includes a comprehensive test suite to ensure reliability and quality.

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage report
pytest --cov=fastapi_agent --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py

# Generate HTML coverage report
pytest --cov=fastapi_agent --cov-report=html
```

### Test Coverage

- **77 tests** covering authentication detection, route discovery, and agent orchestration
- **79% overall coverage** with critical components at 80%+ coverage
- All external dependencies (LLM calls, HTTP requests) are mocked for fast, reliable tests

## 📜 License

This project is licensed under the MIT License.
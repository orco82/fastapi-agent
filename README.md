# 🤖 FastAPI Agent

> 💬 **Talk to your FastAPI app like it's a teammate.**

FastAPI Agent integrates an AI Agent into your FastAPI application.  
It allows interaction with your API endpoints through a chat interface or directly via the `/agent/query` API route.

## ⚙️ Installation:

To install the package, run:
```bash
pip install fastapi_agent
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
    description="some app description",
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

<br>

> 💡 _You can also add custom routes using agent.chat() methode - [Example](https://github.com/orco82/fastapi-agent/blob/main/examples/3_fastapi_agent_example.py)_
 

## 🧩 Additional Arguments:
If your application routes use **Depends** (e.g., an API key), you can pass a dictionary of headers.  
The agent will use them to call your routes and apply the same dependencies to the `/agent/query` route.

```python
api_key = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
    base_url="https://localhost:8000",
    deps={"api-key": api_key},
    include_router=True,
)
```

---

You can also pass the `ignore_routes` argument to prevent the agent from accessing specific routes in your application:

```python

FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
    base_url="https://localhost:8000",
    ignore_routes=["/user/delete/{user_id}"],
    include_router=True,
)

```

## 📁 Additional Examples:

Check out our examples for [ai_agent](https://github.com/orco82/fastapi-agent/blob/main/examples/1_ai_agent_example.py), 
[fastapi_discovery](https://github.com/orco82/fastapi-agent/blob/main/examples/2_fastapi_discovery_example.py), 
and [fastapi_agent](https://github.com/orco82/fastapi-agent/blob/main/examples/3_fastapi_agent_example.py).  
All examples are available [here](https://github.com/orco82/fastapi-agent/blob/main/examples/).

---

#### If you're using *Depends* in your routes, make sure to pass the required headers when calling the `/agent/query` endpoint like the examples below:

#### python
```python
import requests

res = requests.post(
    "http://127.0.0.1:8000/agent/query", 
    json={"query": "show all endpoints"},
    headers={"deps": '{"api-key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}'}
)
print(res.json())
```

#### curl
```bash
curl -k -X POST "http://127.0.0.1:8000/agent/query" \
  -H 'deps: {"api-key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}' \
  -H "Content-Type: application/json" \
  -d '{"query": "show all endpoints"}'
```

## 📜 License

This project is licensed under the MIT License.
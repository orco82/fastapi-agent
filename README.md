# FastAPI Agent

Interact with your FastAPI endpoints using an AI-based chat interface.
FastAPI Agent adds an AI Agent to your FastAPI application. The agent knows how to interact with your API endpoints within a chat interface or with an API route (/agent/query).

## Installation:

To install the dependencies, run:
```bash
pip install fastapi_agent
```

## Usage:

To use the FastAPI Agent, initialize it with your FastAPI app and model. You can add agent routes to your app and interact with the agent through chat.

## Example:

Here is an example of how to use the FastAPI Agent with your FastAPI application:

```python
import uvicorn
from fastapi import FastAPI
from fastapi_agent import FastAPIAgent

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

# add the FastAPI Agent + routes
agent = FastAPIAgent(
    app,
    model="openai:gpt-4o",
    base_url="http://localhost:8000",
    include_router=True,
)

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Additional Examples:

use /agent/query with dependecies
```bash
curl -k -X POST "http://127.0.0.1:8000/agent/query" \
  -H 'deps: {"api-key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}' \
  -H "Content-Type: application/json" \
  -d '{"query": "show all endpoints"}'
```

## License

This project is licensed under the MIT License.
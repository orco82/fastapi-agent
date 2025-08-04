import asyncio
from typing import Any

import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel

from examples.fastapi_app import app
from fastapi_agent import FastAPIAgent

load_dotenv()

agent = FastAPIAgent(
    app,
    model="openai:gpt-4.1-mini",
)

# add default agent.router (routes)
app.include_router(agent.router)


## create custome route using agent.chat()

class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    response: Any
    status: str = "success"


@app.post("/simple_chat", tags=["AI Agent"], response_model=ChatResponse)
async def query_ai_agent(request: ChatRequest):
    response, history = await agent.chat(request.query)
    return ChatResponse(response=response)


async def query(question):
    res, h = await agent.chat(question)
    print(f"\n{res}")


if __name__ == "__main__":
    q = "show all your API endpoint and what you can do"
    asyncio.run(query(q))

uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio

import uvicorn
from dotenv import load_dotenv

from examples.fastapi_app import app
from fastapi_agent import FastAPIAgent

load_dotenv()

agent = FastAPIAgent(
    app,
    model="openai:gpt-4",
)

# add default agent.router (routes)
app.include_router(agent.router)


# create custome route using agent.chat()
@app.post("/simple_chat", tags=["AI Agent"])
async def query_ai_agent(request):
    response, history = await agent.chat(request.query)
    return {
        "query": request.query,
        "response": response,
        "status": "success",
    }


async def query(question):
    res, h = await agent.chat(question)
    print(f"\n{res}")


if __name__ == "__main__":
    q = "show all your API endpoint and what you can do"
    asyncio.run(query(q))

uvicorn.run(app, host="0.0.0.0", port=8000)

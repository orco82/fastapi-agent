import asyncio

import uvicorn
from gen_ai_hub.proxy.native.openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from examples.fastapi_app import app
from fastapi_agent import FastAPIAgent

client = AsyncOpenAI(api_version="2024-10-21")
provider = OpenAIProvider(openai_client=client)
model = OpenAIModel(
    "gpt-4o",
    provider=provider,
)

agent = FastAPIAgent(
    app,
    model=model,
    include_router=True
)


async def main(question):
    res, h = await agent.chat(question)
    print(f"\n{res}")


if __name__ == "__main__":
    q = "show all your endpoint and what you can do"
    asyncio.run(main(q))

uvicorn.run(app, host="0.0.0.0", port=8000)

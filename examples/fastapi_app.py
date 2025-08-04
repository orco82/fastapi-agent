# integration_example.py
# Example of how to integrate the FastAPI Agent with your existing FastAPI app

from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from gen_ai_hub.proxy.native.openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from fastapi_agent import FastAPIAgent
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running Example FastAPI app from \"FastAPI Agent\"")
    yield


# Your existing FastAPI app
app = FastAPI(
    title="User Management",
    version="1.0.0",
    description="A comprehensive business user management API",
    lifespan=lifespan
)

users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
]


# Example Pydantic models
class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


# Your existing routes
@app.get("/")
async def root():
    """Welcome endpoint that returns basic API information"""
    return {"message": "Welcome to My Business API"}


@app.get("/users", response_model=List[UserResponse], tags=["users"])
async def list_users():  # skip: int = 0, limit: int = 10):
    """
    Retrieve a list of users with pagination.
    This endpoint allows you to get multiple users at once.
    """
    global users_db
    # Mock data - replace with your actual database logic
    return users_db  # [skip:skip + limit]


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: int):
    """
    Get a specific user by their unique ID.
    Returns detailed information about a single user.
    """
    global users_db
    user = [u for u in users_db if u["id"] == user_id][0]
    return user


@app.post("/users", response_model=UserResponse, tags=["users"])
async def create_user(user: User):
    """
    Create a new user in the system.
    Provide name, email, and optionally age to create a user account.
    """
    global users_db
    # Mock creation - replace with your actual database logic
    new_user = {"id": (len(users_db) + 1), **user.model_dump()}
    users_db.append(new_user)
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(user_id: int, user: dict):
    """
    Update an existing user's information.
    All fields can be modified using this endpoint.
    """
    global users_db
    print("user_dump:", user)
    _user = [u for u in users_db if u["id"] == user_id][0]
    _user.update(user)
    print("USER:", _user)
    # updated_user = {"id": user_id, **user.model_dump()}
    return _user


@app.delete("/users/{user_id}", tags=["users"])
async def delete_user(user_id: int):
    """
    Delete a user from the system.
    This action cannot be undone.
    """
    global users_db
    users_db = [user for user in users_db if user["id"] != user_id]
    print(users_db)
    return {"message": f"User {user_id} has been deleted"}


if __name__ == "__main__":
    # create model for SAP ai-core
    client = AsyncOpenAI(api_version="2024-10-21")
    provider = OpenAIProvider(openai_client=client)
    model = OpenAIModel(
        "gpt-4o",
        provider=provider,
    )

    # # create model for ollama server
    # model = OpenAIModel(
    #     "ollama3.2:3d",
    #     base_url="http://localhost:11434/v1"
    # )

    # create the FastAPI Agent instance
    agent = FastAPIAgent(
        app,
        model=model,
    )
    app.include_router(agent.router)

    # run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)

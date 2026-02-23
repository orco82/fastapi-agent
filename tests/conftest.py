"""Shared test fixtures for FastAPI Agent test suite"""

from typing import List, Optional
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPBasic, HTTPBearer
from pydantic import BaseModel


# Mock Pydantic models for testing
class User(BaseModel):
    """Mock user model for testing"""

    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    """Mock user response model for testing"""

    id: int
    name: str
    email: str
    age: Optional[int] = None


# Mock database
@pytest.fixture
def users_db():
    """Mock users database"""
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
    ]


# FastAPI apps with different auth patterns
@pytest.fixture
def app_no_auth(users_db):
    """FastAPI app without authentication"""
    app = FastAPI(title="Test API", version="1.0.0", description="Test API without auth")

    @app.get("/")
    async def root():
        """Welcome endpoint"""
        return {"message": "Welcome"}

    @app.get("/users", response_model=List[UserResponse])
    async def list_users():
        """Get all users"""
        return users_db

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int):
        """Get user by ID"""
        user = [u for u in users_db if u["id"] == user_id][0]
        return user

    @app.post("/users", response_model=UserResponse)
    async def create_user(user: User):
        """Create a new user"""
        new_user = {"id": len(users_db) + 1, **user.model_dump()}
        users_db.append(new_user)
        return new_user

    return app


@pytest.fixture
def app_bearer_auth(users_db):
    """FastAPI app with HTTP Bearer authentication"""
    from fastapi.security import HTTPAuthorizationCredentials

    app = FastAPI(title="Bearer Auth API", version="1.0.0")
    security = HTTPBearer()

    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify bearer token"""
        if credentials.credentials != "valid_token":
            raise Exception("Invalid token")
        return credentials

    @app.get("/")
    async def root():
        """Public endpoint"""
        return {"message": "Welcome"}

    @app.get("/users", response_model=List[UserResponse])
    async def list_users(token: HTTPAuthorizationCredentials = Depends(verify_token)):
        """Get all users - requires auth"""
        return users_db

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int, token: HTTPAuthorizationCredentials = Depends(verify_token)):
        """Get user by ID - requires auth"""
        user = [u for u in users_db if u["id"] == user_id][0]
        return user

    @app.post("/users", response_model=UserResponse)
    async def create_user(user: User, token: HTTPAuthorizationCredentials = Depends(verify_token)):
        """Create user - requires auth"""
        new_user = {"id": len(users_db) + 1, **user.model_dump()}
        users_db.append(new_user)
        return new_user

    return app


@pytest.fixture
def app_apikey_header(users_db):
    """FastAPI app with API Key in header authentication"""
    app = FastAPI(title="API Key Header API", version="1.0.0")
    api_key_header = APIKeyHeader(name="X-API-Key")

    def verify_api_key(api_key: str = Depends(api_key_header)):
        """Verify API key"""
        if api_key != "valid_api_key":
            raise Exception("Invalid API key")
        return api_key

    @app.get("/")
    async def root():
        """Public endpoint"""
        return {"message": "Welcome"}

    @app.get("/users", response_model=List[UserResponse])
    async def list_users(api_key=Depends(verify_api_key)):
        """Get all users - requires API key"""
        return users_db

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int, api_key=Depends(verify_api_key)):
        """Get user by ID - requires API key"""
        user = [u for u in users_db if u["id"] == user_id][0]
        return user

    return app


@pytest.fixture
def app_apikey_query(users_db):
    """FastAPI app with API Key in query parameter authentication"""
    app = FastAPI(title="API Key Query API", version="1.0.0")
    api_key_query = APIKeyQuery(name="api_key")

    def verify_api_key(api_key: str = Depends(api_key_query)):
        """Verify API key"""
        if api_key != "valid_api_key":
            raise Exception("Invalid API key")
        return api_key

    @app.get("/")
    async def root():
        """Public endpoint"""
        return {"message": "Welcome"}

    @app.get("/users", response_model=List[UserResponse])
    async def list_users(key=Depends(verify_api_key)):
        """Get all users - requires API key in query"""
        return users_db

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int, key=Depends(verify_api_key)):
        """Get user by ID - requires API key in query"""
        user = [u for u in users_db if u["id"] == user_id][0]
        return user

    return app


@pytest.fixture
def app_basic_auth(users_db):
    """FastAPI app with HTTP Basic authentication"""
    app = FastAPI(title="Basic Auth API", version="1.0.0")
    security = HTTPBasic()

    def verify_credentials(credentials=Depends(security)):
        """Verify basic auth credentials"""
        if credentials.username != "user" or credentials.password != "pass":
            raise Exception("Invalid credentials")
        return credentials

    @app.get("/")
    async def root():
        """Public endpoint"""
        return {"message": "Welcome"}

    @app.get("/users", response_model=List[UserResponse])
    async def list_users(creds=Depends(verify_credentials)):
        """Get all users - requires basic auth"""
        return users_db

    return app


@pytest.fixture
def app_multiple_auth(users_db):
    """FastAPI app with multiple authentication methods (for voting test)"""
    from fastapi.security import HTTPAuthorizationCredentials

    app = FastAPI(title="Multi Auth API", version="1.0.0")

    # Bearer auth (used most frequently)
    bearer = HTTPBearer()

    def verify_bearer(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
        return credentials

    # API Key header (used less frequently)
    api_key = APIKeyHeader(name="X-API-Key")

    def verify_api_key(key: str = Depends(api_key)):
        return key

    # Most routes use bearer
    @app.get("/users", response_model=List[UserResponse])
    async def list_users(token: HTTPAuthorizationCredentials = Depends(verify_bearer)):
        return users_db

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int, token: HTTPAuthorizationCredentials = Depends(verify_bearer)):
        user = [u for u in users_db if u["id"] == user_id][0]
        return user

    @app.post("/users", response_model=UserResponse)
    async def create_user(user: User, token: HTTPAuthorizationCredentials = Depends(verify_bearer)):
        new_user = {"id": len(users_db) + 1, **user.model_dump()}
        users_db.append(new_user)
        return new_user

    # One route uses API key
    @app.get("/admin/stats")
    async def admin_stats(key: str = Depends(verify_api_key)):
        return {"total_users": len(users_db)}

    return app


# Mock fixtures for HTTP responses
@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response"""

    def _create_response(status_code=200, json_data=None, text_data=None):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json = Mock(return_value=json_data or {})
        mock_response.text = text_data or ""
        mock_response.headers = {"content-type": "application/json"}
        return mock_response

    return _create_response


@pytest.fixture
def mock_httpx_client(mock_http_response):
    """Create a mock httpx.AsyncClient"""
    mock_client = AsyncMock()

    # Setup default responses for common methods
    mock_client.get.return_value = mock_http_response(200, {"message": "success"})
    mock_client.post.return_value = mock_http_response(201, {"id": 1, "status": "created"})
    mock_client.put.return_value = mock_http_response(200, {"status": "updated"})
    mock_client.delete.return_value = mock_http_response(200, {"status": "deleted"})
    mock_client.patch.return_value = mock_http_response(200, {"status": "patched"})

    return mock_client


# Mock fixtures for LLM responses
@pytest.fixture
def mock_llm_result():
    """Create a mock LLM result from pydantic-ai"""

    def _create_result(output_text="Mock response from LLM"):
        result = Mock()
        result.output = output_text
        return result

    return _create_result


@pytest.fixture
def mock_pydantic_agent(mock_llm_result):
    """Create a mock pydantic-ai agent"""
    mock_agent = AsyncMock()
    mock_agent.run.return_value = mock_llm_result("This is a test response")
    mock_agent.tool = Mock(side_effect=lambda func: func)  # Pass through decorator
    return mock_agent

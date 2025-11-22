# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Global pytest configuration and shared fixtures for all test suites.
"""

import os
from typing import Any, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService

from app.agent import root_agent
from app.agent_engine_app import AgentEngineApp


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Set up test environment variables."""
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    yield


@pytest.fixture
def mock_google_auth() -> Generator[tuple[MagicMock, str], None, None]:
    """Mock google.auth.default to avoid authentication during tests."""
    with patch("google.auth.default") as mock_auth:
        mock_credentials = MagicMock()
        project_id = "test-project-123"
        mock_auth.return_value = (mock_credentials, project_id)
        yield mock_credentials, project_id


@pytest.fixture
def mock_vertexai() -> Generator[MagicMock, None, None]:
    """Mock vertexai initialization."""
    with patch("vertexai.init") as mock_init:
        yield mock_init


@pytest.fixture
def mock_storage_client() -> Generator[MagicMock, None, None]:
    """Mock Google Cloud Storage client."""
    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_client.return_value.get_bucket.return_value = mock_bucket
        mock_client.return_value.bucket.return_value = mock_bucket
        yield mock_client


@pytest.fixture
def mock_logging_client() -> Generator[MagicMock, None, None]:
    """Mock Google Cloud Logging client."""
    with patch("google.cloud.logging.Client") as mock_client:
        mock_logger = MagicMock()
        mock_client.return_value.logger.return_value = mock_logger
        yield mock_client


@pytest.fixture
def test_agent() -> Agent:
    """Create a test agent instance."""
    return root_agent


@pytest.fixture
def agent_app() -> AgentEngineApp:
    """Create an AgentEngineApp instance for testing."""
    with patch("google.cloud.logging.Client"):
        with patch("app.agent_engine_app.CloudTraceLoggingSpanExporter"):
            app = AgentEngineApp(agent=root_agent)
            app.set_up()
            return app


@pytest.fixture
def session_service() -> InMemorySessionService:
    """Create an in-memory session service for testing."""
    return InMemorySessionService()


@pytest.fixture
def test_session(session_service: InMemorySessionService) -> Any:
    """Create a test session."""
    return session_service.create_session(user_id="test_user", app_name="test_app")


@pytest.fixture
def mock_agent_response() -> dict[str, Any]:
    """Mock agent response data."""
    return {
        "content": {
            "role": "model",
            "parts": [{"text": "This is a test response from the agent."}],
        },
        "metadata": {"model": "gemini-2.0-flash", "finish_reason": "STOP"},
    }


@pytest.fixture
def sample_weather_queries() -> list[str]:
    """Sample weather-related queries for testing."""
    return [
        "What's the weather in San Francisco?",
        "Tell me the weather in SF",
        "How's the weather in New York?",
        "Is it sunny in Los Angeles?",
    ]


@pytest.fixture
def sample_time_queries() -> list[str]:
    """Sample time-related queries for testing."""
    return [
        "What time is it in San Francisco?",
        "Tell me the current time in SF",
        "What's the time in New York?",
    ]


@pytest.fixture
def sample_feedback_data() -> dict[str, Any]:
    """Sample feedback data for testing."""
    return {
        "score": 5,
        "text": "Excellent response!",
        "invocation_id": "test-run-12345",
        "user_id": "test_user",
    }


@pytest.fixture
def mock_span() -> Mock:
    """Mock OpenTelemetry span for testing."""
    mock_span = Mock()
    mock_span.get_span_context.return_value = Mock(
        trace_id=123456789, span_id=987654321
    )
    mock_span.to_json.return_value = '{"name": "test_span", "attributes": {}}'
    return mock_span


@pytest.fixture
def cleanup_env_vars() -> Generator[None, None, None]:
    """Clean up environment variables after test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

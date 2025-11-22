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

"""Mock objects for testing agent components."""

from typing import Any
from unittest.mock import MagicMock, Mock

from google.adk.agents import Agent
from google.genai import types


class MockAgentResponse:
    """Mock agent response for testing."""

    def __init__(
        self,
        text: str = "Mock response",
        role: str = "model",
        finish_reason: str = "STOP",
    ):
        self.text = text
        self.role = role
        self.finish_reason = finish_reason

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "content": {"role": self.role, "parts": [{"text": self.text}]},
            "metadata": {"finish_reason": self.finish_reason},
        }

    def to_event(self) -> dict[str, Any]:
        """Convert to event format compatible with ADK."""
        return {
            "content": types.Content(
                role=self.role, parts=[types.Part.from_text(text=self.text)]
            ),
            "metadata": {"finish_reason": self.finish_reason},
        }


class MockStorageClient:
    """Mock Google Cloud Storage client for testing."""

    def __init__(self) -> None:
        self.buckets: dict[str, MockBucket] = {}

    def get_bucket(self, bucket_name: str) -> "MockBucket":
        """Get or create a mock bucket."""
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = MockBucket(bucket_name)
        return self.buckets[bucket_name]

    def bucket(self, bucket_name: str) -> "MockBucket":
        """Get or create a mock bucket."""
        return self.get_bucket(bucket_name)

    def create_bucket(
        self, bucket_name: str, location: str = "us-central1", project: str = ""
    ) -> "MockBucket":
        """Create a mock bucket."""
        bucket = MockBucket(bucket_name, location=location, project=project)
        self.buckets[bucket_name] = bucket
        return bucket


class MockBucket:
    """Mock GCS bucket."""

    def __init__(
        self, name: str, location: str = "us-central1", project: str = "test-project"
    ):
        self.name = name
        self.location = location
        self.project = project
        self.blobs: dict[str, MockBlob] = {}
        self._exists = True

    def exists(self) -> bool:
        """Check if bucket exists."""
        return self._exists

    def blob(self, blob_name: str) -> "MockBlob":
        """Get or create a mock blob."""
        if blob_name not in self.blobs:
            self.blobs[blob_name] = MockBlob(blob_name, self)
        return self.blobs[blob_name]


class MockBlob:
    """Mock GCS blob."""

    def __init__(self, name: str, bucket: MockBucket):
        self.name = name
        self.bucket = bucket
        self.content: bytes = b""
        self.content_type: str = ""

    def upload_from_string(self, data: str | bytes, content_type: str = "") -> None:
        """Mock upload from string."""
        self.content = data.encode() if isinstance(data, str) else data
        self.content_type = content_type

    def download_as_string(self) -> bytes:
        """Mock download as string."""
        return self.content


class MockCloudLoggingClient:
    """Mock Google Cloud Logging client."""

    def __init__(self, project: str = "test-project"):
        self.project = project
        self.logs: list[dict[str, Any]] = []
        self._logger = MockLogger(self)

    def logger(self, name: str) -> "MockLogger":
        """Get a mock logger."""
        return self._logger


class MockLogger:
    """Mock Cloud Logging logger."""

    def __init__(self, client: MockCloudLoggingClient):
        self.client = client
        self.entries: list[dict[str, Any]] = []

    def log_struct(
        self,
        info: dict[str, Any],
        severity: str = "INFO",
        labels: dict[str, str] | None = None,
    ) -> None:
        """Mock structured logging."""
        entry = {"info": info, "severity": severity, "labels": labels or {}}
        self.entries.append(entry)
        self.client.logs.append(entry)


class MockSpan:
    """Mock OpenTelemetry span."""

    def __init__(
        self,
        name: str,
        trace_id: int = 123456789,
        span_id: int = 987654321,
        attributes: dict[str, Any] | None = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.attributes = attributes or {}
        self._context = Mock()
        self._context.trace_id = trace_id
        self._context.span_id = span_id

    def get_span_context(self) -> Any:
        """Get span context."""
        return self._context

    def to_json(self) -> str:
        """Convert to JSON."""
        import json

        return json.dumps({"name": self.name, "attributes": self.attributes})


def create_mock_agent(
    name: str = "test_agent",
    model: str = "gemini-2.0-flash",
    instruction: str = "Test agent",
) -> Mock:
    """Create a mock agent for testing."""
    mock_agent = Mock(spec=Agent)
    mock_agent.name = name
    mock_agent.model = model
    mock_agent.instruction = instruction
    mock_agent.tools = []
    return mock_agent


def create_mock_session(
    session_id: str = "test-session-123", user_id: str = "test-user"
) -> Mock:
    """Create a mock session for testing."""
    mock_session = Mock()
    mock_session.id = session_id
    mock_session.user_id = user_id
    mock_session.app_name = "test_app"
    mock_session.state = {}
    return mock_session


def create_mock_runner(agent: Any = None) -> Mock:
    """Create a mock runner for testing."""
    mock_runner = Mock()
    mock_runner.agent = agent or create_mock_agent()

    def mock_run(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [MockAgentResponse().to_event()]

    mock_runner.run = mock_run
    return mock_runner


def create_mock_event(
    text: str = "Test response", role: str = "model", event_type: str = "content"
) -> dict[str, Any]:
    """Create a mock event for testing."""
    return {
        "type": event_type,
        "content": types.Content(
            role=role, parts=[types.Part.from_text(text=text)]
        ),
    }

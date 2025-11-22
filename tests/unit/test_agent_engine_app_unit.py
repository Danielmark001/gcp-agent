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

"""Unit tests for AgentEngineApp."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.agent import root_agent
from app.agent_engine_app import AgentEngineApp
from tests.utils.mocks import MockLogger


class TestAgentEngineApp:
    """Tests for AgentEngineApp class."""

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_initialization(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test AgentEngineApp initialization."""
        app = AgentEngineApp(agent=root_agent)
        assert app is not None

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_set_up(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test set_up method."""
        mock_logger = MagicMock()
        mock_logging_client.return_value.logger.return_value = mock_logger

        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        # Should create logger
        assert app.logger == mock_logger

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_register_feedback_valid(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test registering valid feedback."""
        mock_logger = MockLogger(MagicMock())
        mock_logging_client.return_value.logger.return_value = mock_logger

        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        feedback_data = {
            "score": 5,
            "text": "Great!",
            "invocation_id": "test-123",
        }

        app.register_feedback(feedback_data)

        # Should log the feedback
        assert len(mock_logger.entries) > 0
        logged_entry = mock_logger.entries[0]
        assert logged_entry["severity"] == "INFO"
        assert logged_entry["info"]["score"] == 5

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_register_feedback_invalid(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test registering invalid feedback raises error."""
        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        invalid_feedback = {
            "score": "invalid",  # Should be numeric
            "invocation_id": "test-123",
        }

        with pytest.raises(ValidationError):
            app.register_feedback(invalid_feedback)

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_register_feedback_missing_required_field(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test registering feedback with missing required field."""
        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        incomplete_feedback = {
            "score": 5,
            # Missing invocation_id
        }

        with pytest.raises(ValidationError):
            app.register_feedback(incomplete_feedback)

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_register_operations(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test register_operations includes feedback."""
        app = AgentEngineApp(agent=root_agent)

        operations = app.register_operations()

        # Should include register_feedback in operations
        assert "" in operations
        assert "register_feedback" in operations[""]

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_clone(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test cloning the agent app."""
        app = AgentEngineApp(agent=root_agent)
        cloned_app = app.clone()

        assert cloned_app is not None
        assert isinstance(cloned_app, AgentEngineApp)
        assert cloned_app is not app  # Should be a different instance

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_feedback_with_all_optional_fields(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test registering feedback with all optional fields."""
        mock_logger = MockLogger(MagicMock())
        mock_logging_client.return_value.logger.return_value = mock_logger

        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        feedback_data = {
            "score": 4.5,
            "text": "Very good response",
            "invocation_id": "test-456",
            "user_id": "user-789",
            "log_type": "feedback",
            "service_name": "my-agent",
        }

        app.register_feedback(feedback_data)

        assert len(mock_logger.entries) > 0
        logged_entry = mock_logger.entries[0]
        assert logged_entry["info"]["score"] == 4.5
        assert logged_entry["info"]["text"] == "Very good response"
        assert logged_entry["info"]["user_id"] == "user-789"

    @patch("app.agent_engine_app.CloudTraceLoggingSpanExporter")
    @patch("google.cloud.logging.Client")
    def test_multiple_feedback_submissions(
        self, mock_logging_client: MagicMock, mock_exporter: MagicMock
    ) -> None:
        """Test submitting multiple feedback entries."""
        mock_logger = MockLogger(MagicMock())
        mock_logging_client.return_value.logger.return_value = mock_logger

        app = AgentEngineApp(agent=root_agent)
        app.set_up()

        for i in range(5):
            feedback_data = {
                "score": i + 1,
                "text": f"Feedback {i}",
                "invocation_id": f"test-{i}",
            }
            app.register_feedback(feedback_data)

        # Should have logged all 5 feedback entries
        assert len(mock_logger.entries) == 5

        # Verify each entry
        for i, entry in enumerate(mock_logger.entries):
            assert entry["info"]["score"] == i + 1
            assert entry["info"]["text"] == f"Feedback {i}"

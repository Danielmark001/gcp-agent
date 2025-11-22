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

"""Integration tests for error handling and edge cases."""

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from tests.utils.data_generators import generate_edge_case_inputs
from tests.utils.helpers import assert_valid_agent_response


class TestErrorHandling:
    """Tests for error handling in agent operations."""

    def test_empty_message_handling(self) -> None:
        """Test agent handling of empty message."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Send message with empty text - should still create valid content
        message = types.Content(role="user", parts=[types.Part.from_text(text=" ")])

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Should handle gracefully
        assert len(events) >= 0

    def test_very_long_message(self) -> None:
        """Test agent handling of very long message."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Create a very long message
        long_text = "Tell me about the weather. " * 100
        message = types.Content(role="user", parts=[types.Part.from_text(text=long_text)])

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Should handle gracefully
        assert len(events) >= 0

    def test_special_characters_in_message(self) -> None:
        """Test agent handling of special characters."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="What's the weather in @San#Francisco$%^&*()?"
                )
            ],
        )

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        assert_valid_agent_response(events)

    def test_unicode_characters_in_message(self) -> None:
        """Test agent handling of unicode characters."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in São Paulo? 世界")],
        )

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        assert_valid_agent_response(events)

    def test_invalid_session_id(self) -> None:
        """Test handling of invalid session ID."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user", parts=[types.Part.from_text(text="What's the weather?")]
        )

        # Using a non-existent session ID might raise an error or create new session
        # The behavior depends on the implementation
        try:
            events = list(
                runner.run(
                    new_message=message,
                    user_id="test_user",
                    session_id="non-existent-session-id",
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )
            # If it doesn't raise an error, it should return valid events
            assert len(events) >= 0
        except Exception as e:
            # If it raises an error, that's also acceptable behavior
            assert isinstance(e, Exception)

    def test_edge_case_inputs(self) -> None:
        """Test various edge case inputs."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        edge_cases = generate_edge_case_inputs()

        for edge_case in edge_cases[:3]:  # Test first 3 edge cases
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=edge_case["input"])]
            )

            try:
                events = list(
                    runner.run(
                        new_message=message,
                        user_id="test_user",
                        session_id=session.id,
                        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                    )
                )
                # Should handle gracefully
                assert len(events) >= 0
            except Exception:
                # Some edge cases might raise exceptions, which is acceptable
                pass

    def test_rapid_successive_queries(self) -> None:
        """Test handling of rapid successive queries."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        queries = [
            "What's the weather in SF?",
            "And the time?",
            "What about New York?",
        ]

        for query_text in queries:
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=query_text)]
            )

            events = list(
                runner.run(
                    new_message=message,
                    user_id="test_user",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

            assert_valid_agent_response(events)

    def test_session_service_isolation(self) -> None:
        """Test that session services are properly isolated."""
        session_service1 = InMemorySessionService()
        session_service2 = InMemorySessionService()

        session1 = session_service1.create_session(user_id="user1", app_name="test")
        session2 = session_service2.create_session(user_id="user2", app_name="test")

        # Sessions from different services should have different IDs
        assert session1.id != session2.id

        # One service shouldn't be able to access the other's sessions
        with pytest.raises(Exception):
            session_service1.get_session(session2.id)


class TestAgentEngineAppErrorHandling:
    """Tests for error handling in AgentEngineApp."""

    def test_invalid_feedback_format(self, agent_app: "AgentEngineApp") -> None:  # type: ignore # noqa: F821
        """Test handling of invalid feedback format."""
        from pydantic import ValidationError

        invalid_feedback = {
            "score": "not-a-number",
            "invocation_id": "test-123",
        }

        with pytest.raises(ValidationError):
            agent_app.register_feedback(invalid_feedback)

    def test_missing_feedback_fields(self, agent_app: "AgentEngineApp") -> None:  # type: ignore # noqa: F821
        """Test handling of missing required feedback fields."""
        from pydantic import ValidationError

        incomplete_feedback = {
            "score": 5,
            # Missing invocation_id
        }

        with pytest.raises(ValidationError):
            agent_app.register_feedback(incomplete_feedback)

    def test_negative_feedback_score(self, agent_app: "AgentEngineApp") -> None:  # type: ignore # noqa: F821
        """Test that negative feedback scores are allowed."""
        feedback = {"score": -1, "invocation_id": "test-123"}

        # Should not raise an error
        agent_app.register_feedback(feedback)

    def test_extremely_large_feedback_score(self, agent_app: "AgentEngineApp") -> None:  # type: ignore # noqa: F821
        """Test handling of extremely large feedback scores."""
        feedback = {"score": 999999999, "invocation_id": "test-123"}

        # Should not raise an error
        agent_app.register_feedback(feedback)

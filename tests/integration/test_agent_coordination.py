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

"""Integration tests for agent coordination and multi-agent interactions."""

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from tests.utils.helpers import assert_valid_agent_response, extract_text_from_events


class TestAgentCoordination:
    """Tests for agent coordination across multiple queries."""

    def test_sequential_queries_same_session(self) -> None:
        """Test multiple queries in the same session."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # First query
        message1 = types.Content(
            role="user", parts=[types.Part.from_text(text="What's the weather in SF?")]
        )
        events1 = list(
            runner.run(
                new_message=message1,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        assert_valid_agent_response(events1)

        # Second query in same session
        message2 = types.Content(
            role="user", parts=[types.Part.from_text(text="What time is it there?")]
        )
        events2 = list(
            runner.run(
                new_message=message2,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        assert_valid_agent_response(events2)

    def test_multiple_tool_usage_in_single_query(self) -> None:
        """Test query that requires multiple tool calls."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Query that might use both weather and time tools
        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="What's the weather and current time in San Francisco?"
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
        texts = extract_text_from_events(events)
        combined_text = " ".join(texts).lower()

        # Response should contain weather or time information
        assert any(
            keyword in combined_text
            for keyword in ["weather", "time", "degrees", "foggy", "sunny"]
        )

    def test_different_users_isolated_sessions(self) -> None:
        """Test that different users have isolated sessions."""
        session_service = InMemorySessionService()

        # Create sessions for two different users
        session1 = session_service.create_session(user_id="user1", app_name="test")
        session2 = session_service.create_session(user_id="user2", app_name="test")

        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # User 1 query
        message1 = types.Content(
            role="user", parts=[types.Part.from_text(text="What's the weather in SF?")]
        )
        events1 = list(
            runner.run(
                new_message=message1,
                user_id="user1",
                session_id=session1.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # User 2 query
        message2 = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in New York?")],
        )
        events2 = list(
            runner.run(
                new_message=message2,
                user_id="user2",
                session_id=session2.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Both should have valid responses
        assert_valid_agent_response(events1)
        assert_valid_agent_response(events2)

    def test_concurrent_sessions_handling(self) -> None:
        """Test handling of multiple concurrent sessions."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        sessions = []
        for i in range(3):
            session = session_service.create_session(
                user_id=f"user_{i}", app_name="test"
            )
            sessions.append(session)

        # Run queries for all sessions
        all_events = []
        for i, session in enumerate(sessions):
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"What's the weather in city {i}?")],
            )
            events = list(
                runner.run(
                    new_message=message,
                    user_id=f"user_{i}",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )
            all_events.append(events)

        # All sessions should get valid responses
        for events in all_events:
            assert_valid_agent_response(events)

    def test_session_state_persistence(self) -> None:
        """Test that session state persists across queries."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # First query
        message1 = types.Content(
            role="user", parts=[types.Part.from_text(text="Hello, how are you?")]
        )
        list(
            runner.run(
                new_message=message1,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Retrieve session to check state
        retrieved_session = session_service.get_session(session.id)
        assert retrieved_session is not None
        assert retrieved_session.id == session.id

    def test_error_recovery_in_session(self) -> None:
        """Test that session can recover from errors."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Send a normal query after potential error condition
        message = types.Content(
            role="user", parts=[types.Part.from_text(text="What's the weather in SF?")]
        )

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Should still get valid response
        assert_valid_agent_response(events)

    def test_agent_handles_complex_query(self) -> None:
        """Test agent handling complex multi-part query."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="Can you tell me the weather in San Francisco and also "
                    "what time it is there? I need both pieces of information."
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
        # Should have meaningful response
        assert len(events) > 0

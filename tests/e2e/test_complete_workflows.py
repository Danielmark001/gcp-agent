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

"""End-to-end tests for complete agent workflows."""

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.agent_engine_app import AgentEngineApp
from tests.utils.helpers import (
    assert_valid_agent_response,
    extract_text_from_events,
)


class TestCompleteAgentWorkflows:
    """End-to-end tests for complete agent workflows."""

    def test_weather_query_workflow(self) -> None:
        """Test complete workflow for weather query."""
        # Setup
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Execute query
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in San Francisco?")],
        )

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Verify
        assert_valid_agent_response(events)
        texts = extract_text_from_events(events)
        combined_text = " ".join(texts).lower()

        # Should mention weather information
        assert any(
            keyword in combined_text
            for keyword in ["weather", "degrees", "foggy", "sunny"]
        )

    def test_time_query_workflow(self) -> None:
        """Test complete workflow for time query."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What time is it in San Francisco?")],
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

        # Should mention time
        assert "time" in combined_text or ":" in combined_text

    def test_multi_turn_conversation_workflow(self) -> None:
        """Test complete workflow for multi-turn conversation."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Turn 1: Ask about weather
        message1 = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in San Francisco?")],
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

        # Turn 2: Follow-up question
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

        # Turn 3: Thank you
        message3 = types.Content(
            role="user", parts=[types.Part.from_text(text="Thank you!")]
        )
        events3 = list(
            runner.run(
                new_message=message3,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        assert_valid_agent_response(events3)

    def test_agent_engine_app_workflow(self, agent_app: AgentEngineApp) -> None:
        """Test complete workflow using AgentEngineApp."""
        # Query the agent
        message = "What's the weather in San Francisco?"
        events = list(agent_app.stream_query(message=message, user_id="test_user"))

        assert_valid_agent_response(events)

        # Submit feedback
        feedback = {
            "score": 5,
            "text": "Great response!",
            "invocation_id": "test-workflow-123",
        }
        agent_app.register_feedback(feedback)

    def test_multi_user_workflow(self) -> None:
        """Test workflow with multiple users."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # User 1
        session1 = session_service.create_session(user_id="user1", app_name="test")
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
        assert_valid_agent_response(events1)

        # User 2
        session2 = session_service.create_session(user_id="user2", app_name="test")
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
        assert_valid_agent_response(events2)

    def test_complex_query_workflow(self) -> None:
        """Test workflow with complex multi-part query."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="I need information about San Francisco. "
                    "Can you tell me what the weather is like and what time it is?"
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
        assert len(events) > 0

    def test_error_recovery_workflow(self) -> None:
        """Test workflow that recovers from potential errors."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Send a potentially problematic query
        message1 = types.Content(
            role="user", parts=[types.Part.from_text(text="")]
        )
        try:
            events1 = list(
                runner.run(
                    new_message=message1,
                    user_id="test_user",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )
        except Exception:
            pass  # Expected to potentially fail

        # Follow up with a normal query
        message2 = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in SF?")],
        )
        events2 = list(
            runner.run(
                new_message=message2,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        # Should recover and provide valid response
        assert_valid_agent_response(events2)

    def test_session_lifecycle_workflow(self) -> None:
        """Test complete session lifecycle."""
        session_service = InMemorySessionService()

        # Create session
        session = session_service.create_session(user_id="test_user", app_name="test")
        assert session is not None
        assert session.id is not None

        # Use session
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")
        message = types.Content(
            role="user", parts=[types.Part.from_text(text="Hello!")]
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

        # Retrieve session
        retrieved_session = session_service.get_session(session.id)
        assert retrieved_session is not None
        assert retrieved_session.id == session.id

    def test_feedback_workflow(self, agent_app: AgentEngineApp) -> None:
        """Test complete feedback submission workflow."""
        # Execute query
        message = "What's the weather in SF?"
        events = list(agent_app.stream_query(message=message, user_id="test_user"))
        assert_valid_agent_response(events)

        # Submit various feedback scores
        for score in [1, 2, 3, 4, 5]:
            feedback = {
                "score": score,
                "text": f"Feedback with score {score}",
                "invocation_id": f"test-{score}",
            }
            agent_app.register_feedback(feedback)

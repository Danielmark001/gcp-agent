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

"""End-to-end tests for multi-agent scenarios."""

import concurrent.futures
from typing import Any

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from tests.utils.data_generators import generate_concurrent_agent_requests
from tests.utils.helpers import assert_valid_agent_response


class TestMultiAgentScenarios:
    """End-to-end tests for multi-agent scenarios."""

    def test_concurrent_queries_different_users(self) -> None:
        """Test concurrent queries from different users."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        def execute_query(user_id: str, query: str) -> list[dict[str, Any]]:
            """Execute a single query."""
            session = session_service.create_session(
                user_id=user_id, app_name="test"
            )
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )
            return list(
                runner.run(
                    new_message=message,
                    user_id=user_id,
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

        # Execute multiple queries concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    execute_query, f"user_{i}", "What's the weather in SF?"
                )
                for i in range(3)
            ]

            results = [future.result() for future in futures]

        # All queries should complete successfully
        for events in results:
            assert_valid_agent_response(events)

    def test_concurrent_queries_same_user(self) -> None:
        """Test concurrent queries from the same user (different sessions)."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        def execute_query(query: str) -> list[dict[str, Any]]:
            """Execute a single query."""
            session = session_service.create_session(
                user_id="test_user", app_name="test"
            )
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )
            return list(
                runner.run(
                    new_message=message,
                    user_id="test_user",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

        queries = [
            "What's the weather in SF?",
            "What time is it in SF?",
            "What's the weather in New York?",
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_query, query) for query in queries]
            results = [future.result() for future in futures]

        # All queries should complete successfully
        for events in results:
            assert_valid_agent_response(events)

    def test_sequential_multi_user_interactions(self) -> None:
        """Test sequential interactions from multiple users."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        users = ["user_1", "user_2", "user_3"]
        sessions = {
            user: session_service.create_session(user_id=user, app_name="test")
            for user in users
        }

        # Each user sends multiple messages
        for user in users:
            for i in range(2):
                message = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"Query {i} from {user}")],
                )
                events = list(
                    runner.run(
                        new_message=message,
                        user_id=user,
                        session_id=sessions[user].id,
                        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                    )
                )
                assert_valid_agent_response(events)

    def test_load_balanced_queries(self) -> None:
        """Test load balancing across multiple queries."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        requests = generate_concurrent_agent_requests(count=5)

        def execute_request(request: dict[str, Any]) -> list[dict[str, Any]]:
            """Execute a single request."""
            session = session_service.create_session(
                user_id=request["user_id"], app_name="test"
            )
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=request["message"])]
            )
            return list(
                runner.run(
                    new_message=message,
                    user_id=request["user_id"],
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

        # Execute requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_request, req) for req in requests]
            results = [future.result() for future in futures]

        # All requests should complete
        assert len(results) == 5
        for events in results:
            assert_valid_agent_response(events)

    def test_cascading_agent_interactions(self) -> None:
        """Test cascading interactions where one query leads to another."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # First query about weather
        message1 = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in SF?")],
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

        # Based on weather response, ask about time
        message2 = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What time is it there?")],
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

        # Follow-up question
        message3 = types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="Based on the weather, should I bring a jacket?")
            ],
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

    def test_high_concurrency_scenario(self) -> None:
        """Test system behavior under high concurrency."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        def execute_query(index: int) -> list[dict[str, Any]]:
            """Execute a single query."""
            session = session_service.create_session(
                user_id=f"user_{index}", app_name="test"
            )
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Query {index}")],
            )
            return list(
                runner.run(
                    new_message=message,
                    user_id=f"user_{index}",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

        # Execute 10 concurrent queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_query, i) for i in range(10)]
            results = [future.result() for future in futures]

        # All queries should complete
        assert len(results) == 10
        successful_results = [
            events for events in results if len(events) > 0
        ]
        # Most should succeed
        assert len(successful_results) >= 8

    def test_mixed_query_types_concurrent(self) -> None:
        """Test concurrent queries of different types."""
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        queries = [
            "What's the weather in San Francisco?",
            "What time is it in SF?",
            "What's the weather in New York?",
            "Tell me about the weather",
            "What time is it?",
        ]

        def execute_query(user_id: str, query: str) -> list[dict[str, Any]]:
            """Execute a single query."""
            session = session_service.create_session(
                user_id=user_id, app_name="test"
            )
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )
            return list(
                runner.run(
                    new_message=message,
                    user_id=user_id,
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(execute_query, f"user_{i}", query)
                for i, query in enumerate(queries)
            ]
            results = [future.result() for future in futures]

        # All queries should complete
        for events in results:
            assert_valid_agent_response(events)

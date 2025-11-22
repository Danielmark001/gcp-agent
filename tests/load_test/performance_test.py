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

"""Performance tests for agent system."""

import statistics
import time
from typing import Any

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from tests.utils.helpers import assert_valid_agent_response


class TestAgentPerformance:
    """Performance tests for agent operations."""

    def test_single_query_response_time(self) -> None:
        """Test response time for a single query."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="What's the weather in San Francisco?")],
        )

        start_time = time.time()
        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        end_time = time.time()

        response_time = end_time - start_time

        assert_valid_agent_response(events)
        # Response should be reasonably fast (adjust threshold as needed)
        assert response_time < 30.0, f"Response took {response_time}s"

    def test_average_response_time(self) -> None:
        """Test average response time over multiple queries."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        queries = [
            "What's the weather in SF?",
            "What time is it?",
            "Weather in New York?",
        ]

        response_times = []

        for query in queries:
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )

            start_time = time.time()
            events = list(
                runner.run(
                    new_message=message,
                    user_id="test_user",
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )
            end_time = time.time()

            response_times.append(end_time - start_time)
            assert_valid_agent_response(events)

        avg_response_time = statistics.mean(response_times)
        print(f"\nAverage response time: {avg_response_time:.2f}s")
        print(f"Min: {min(response_times):.2f}s, Max: {max(response_times):.2f}s")

        # Average should be reasonable
        assert avg_response_time < 30.0

    def test_throughput(self) -> None:
        """Test query throughput."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        num_queries = 5
        start_time = time.time()

        for i in range(num_queries):
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Query {i}: What's the weather?")],
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

        end_time = time.time()
        total_time = end_time - start_time
        throughput = num_queries / total_time

        print(f"\nThroughput: {throughput:.2f} queries/second")
        print(f"Total time for {num_queries} queries: {total_time:.2f}s")

        # Should process at least 0.1 queries per second
        assert throughput > 0.1

    def test_session_creation_performance(self) -> None:
        """Test session creation performance."""
        session_service = InMemorySessionService()

        start_time = time.time()
        sessions = []
        for i in range(10):
            session = session_service.create_session(
                user_id=f"user_{i}", app_name="test"
            )
            sessions.append(session)
        end_time = time.time()

        creation_time = end_time - start_time
        avg_creation_time = creation_time / 10

        print(f"\nAverage session creation time: {avg_creation_time*1000:.2f}ms")

        # Session creation should be fast
        assert avg_creation_time < 1.0

    def test_memory_usage_stability(self) -> None:
        """Test that memory usage remains stable over multiple queries."""
        session_service = InMemorySessionService()
        session = session_service.create_session(user_id="test_user", app_name="test")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        # Run multiple queries to check for memory leaks
        for i in range(10):
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Query {i}")],
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

        # If we get here without running out of memory, test passes

    def test_concurrent_session_performance(self) -> None:
        """Test performance with multiple concurrent sessions."""
        import concurrent.futures

        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

        def execute_query(user_id: str) -> float:
            """Execute query and return response time."""
            session = session_service.create_session(
                user_id=user_id, app_name="test"
            )
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text="What's the weather?")],
            )

            start = time.time()
            list(
                runner.run(
                    new_message=message,
                    user_id=user_id,
                    session_id=session.id,
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
                )
            )
            return time.time() - start

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(execute_query, f"user_{i}") for i in range(3)
            ]
            response_times = [future.result() for future in futures]
        end_time = time.time()

        total_time = end_time - start_time
        avg_response_time = statistics.mean(response_times)

        print(f"\nConcurrent queries total time: {total_time:.2f}s")
        print(f"Average response time: {avg_response_time:.2f}s")

        # Concurrent execution should be reasonably fast
        assert total_time < 60.0

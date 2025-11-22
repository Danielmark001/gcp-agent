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

"""Data generators for testing."""

import random
import string
import uuid
from typing import Any

from google.genai import types


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length.

    Args:
        length: Length of the string to generate

    Returns:
        Random string
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_query(query_type: str = "general") -> str:
    """Generate a random query for testing.

    Args:
        query_type: Type of query (weather, time, general)

    Returns:
        Random query string
    """
    if query_type == "weather":
        cities = ["San Francisco", "New York", "Los Angeles", "Chicago", "Miami"]
        templates = [
            "What's the weather in {}?",
            "Tell me the weather in {}",
            "How's the weather in {}?",
            "Is it sunny in {}?",
        ]
        return random.choice(templates).format(random.choice(cities))
    elif query_type == "time":
        cities = ["San Francisco", "New York", "Los Angeles", "SF"]
        templates = [
            "What time is it in {}?",
            "Tell me the current time in {}",
            "What's the time in {}?",
        ]
        return random.choice(templates).format(random.choice(cities))
    else:
        templates = [
            "Tell me about {}",
            "Explain {}",
            "What is {}?",
            "How does {} work?",
        ]
        topics = ["AI", "machine learning", "cloud computing", "Python", "testing"]
        return random.choice(templates).format(random.choice(topics))


def generate_session_data(
    user_id: str | None = None, app_name: str = "test_app"
) -> dict[str, Any]:
    """Generate session data for testing.

    Args:
        user_id: User ID (generates random if not provided)
        app_name: Application name

    Returns:
        Session data dictionary
    """
    return {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id or f"user_{generate_random_string(8)}",
        "app_name": app_name,
        "created_at": "2025-01-01T00:00:00Z",
        "state": {},
    }


def generate_feedback_data(
    score: int | None = None,
    invocation_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate feedback data for testing.

    Args:
        score: Feedback score (1-5, random if not provided)
        invocation_id: Invocation ID (generates random if not provided)
        user_id: User ID (generates random if not provided)

    Returns:
        Feedback data dictionary
    """
    return {
        "score": score if score is not None else random.randint(1, 5),
        "text": f"Test feedback {generate_random_string(5)}",
        "invocation_id": invocation_id or f"inv_{uuid.uuid4()}",
        "log_type": "feedback",
        "service_name": "my-agent",
        "user_id": user_id or f"user_{generate_random_string(8)}",
    }


def generate_mock_events(
    count: int = 3, include_tool_calls: bool = False
) -> list[dict[str, Any]]:
    """Generate mock events for testing.

    Args:
        count: Number of events to generate
        include_tool_calls: Whether to include tool call events

    Returns:
        List of mock event dictionaries
    """
    events = []

    for i in range(count):
        event: dict[str, Any] = {
            "type": "content",
            "content": types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text=f"Mock response {i+1}: {generate_random_string(20)}")
                ],
            ),
        }
        events.append(event)

    if include_tool_calls:
        tool_names = ["get_weather", "get_current_time"]
        for tool_name in tool_names:
            tool_event: dict[str, Any] = {
                "type": "tool_call",
                "tool_call": {
                    "name": tool_name,
                    "args": {"query": "San Francisco"},
                },
            }
            events.insert(len(events) // 2, tool_event)

    return events


def generate_agent_config(
    name: str | None = None,
    model: str = "gemini-2.0-flash",
    instruction: str | None = None,
) -> dict[str, Any]:
    """Generate agent configuration for testing.

    Args:
        name: Agent name (generates random if not provided)
        model: Model name
        instruction: Agent instruction (generates default if not provided)

    Returns:
        Agent configuration dictionary
    """
    return {
        "name": name or f"test_agent_{generate_random_string(6)}",
        "model": model,
        "instruction": instruction
        or f"Test agent instruction {generate_random_string(10)}",
        "tools": [],
    }


def generate_error_scenarios() -> list[dict[str, Any]]:
    """Generate error scenarios for testing.

    Returns:
        List of error scenario dictionaries
    """
    return [
        {
            "name": "invalid_input",
            "input": None,
            "expected_error": ValueError,
        },
        {
            "name": "empty_message",
            "input": "",
            "expected_error": ValueError,
        },
        {
            "name": "invalid_user_id",
            "input": {"message": "test", "user_id": None},
            "expected_error": ValueError,
        },
        {
            "name": "malformed_feedback",
            "input": {"score": "invalid", "invocation_id": "test"},
            "expected_error": ValueError,
        },
    ]


def generate_load_test_scenarios(num_scenarios: int = 5) -> list[dict[str, Any]]:
    """Generate load test scenarios.

    Args:
        num_scenarios: Number of scenarios to generate

    Returns:
        List of load test scenario dictionaries
    """
    scenarios = []
    for i in range(num_scenarios):
        scenarios.append(
            {
                "id": f"scenario_{i+1}",
                "user_count": random.randint(1, 100),
                "query_type": random.choice(["weather", "time", "general"]),
                "duration_seconds": random.randint(10, 60),
            }
        )
    return scenarios


def generate_concurrent_agent_requests(
    count: int = 10,
) -> list[dict[str, Any]]:
    """Generate concurrent agent requests for testing.

    Args:
        count: Number of requests to generate

    Returns:
        List of request dictionaries
    """
    requests = []
    for i in range(count):
        requests.append(
            {
                "request_id": str(uuid.uuid4()),
                "message": generate_random_query(),
                "user_id": f"user_{i}",
                "session_id": str(uuid.uuid4()),
            }
        )
    return requests


def generate_multi_agent_scenario() -> dict[str, Any]:
    """Generate a multi-agent interaction scenario.

    Returns:
        Multi-agent scenario dictionary
    """
    return {
        "agents": [
            {
                "name": "coordinator",
                "role": "Coordinates tasks between agents",
                "initial_message": "What's the weather and time in SF?",
            },
            {
                "name": "weather_agent",
                "role": "Provides weather information",
                "expected_tool": "get_weather",
            },
            {
                "name": "time_agent",
                "role": "Provides time information",
                "expected_tool": "get_current_time",
            },
        ],
        "expected_interactions": 3,
        "timeout_seconds": 30,
    }


def generate_edge_case_inputs() -> list[dict[str, Any]]:
    """Generate edge case inputs for testing.

    Returns:
        List of edge case input dictionaries
    """
    return [
        {"name": "empty_string", "input": "", "description": "Empty string input"},
        {
            "name": "very_long_string",
            "input": "A" * 10000,
            "description": "Very long string input",
        },
        {
            "name": "special_characters",
            "input": "!@#$%^&*()_+-=[]{}|;:',.<>?/~`",
            "description": "Special characters",
        },
        {
            "name": "unicode_characters",
            "input": "Hello 世界 🌍 مرحبا",
            "description": "Unicode characters",
        },
        {
            "name": "whitespace_only",
            "input": "   \n\t   ",
            "description": "Whitespace only",
        },
        {
            "name": "null_bytes",
            "input": "test\x00string",
            "description": "String with null bytes",
        },
    ]

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

"""Helper functions for testing."""

import time
from typing import Any, Callable


def extract_text_from_events(events: list[dict[str, Any]]) -> list[str]:
    """Extract text content from a list of events.

    Args:
        events: List of event dictionaries

    Returns:
        List of text strings extracted from events
    """
    texts = []
    for event in events:
        content = event.get("content")
        if content and hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    texts.append(part.text)
    return texts


def assert_valid_agent_response(events: list[dict[str, Any]]) -> None:
    """Assert that events contain a valid agent response.

    Args:
        events: List of event dictionaries

    Raises:
        AssertionError: If response is not valid
    """
    assert len(events) > 0, "Expected at least one event"

    has_text_content = False
    for event in events:
        content = event.get("content")
        if content and hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    has_text_content = True
                    break
        if has_text_content:
            break

    assert has_text_content, "Expected at least one event with text content"


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.1,
    error_message: str = "Condition not met within timeout",
) -> None:
    """Wait for a condition to become true.

    Args:
        condition: Callable that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        error_message: Error message if timeout is reached

    Raises:
        TimeoutError: If condition is not met within timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError(error_message)


def compare_agent_states(state1: dict[str, Any], state2: dict[str, Any]) -> bool:
    """Compare two agent states for equality.

    Args:
        state1: First agent state
        state2: Second agent state

    Returns:
        True if states are equal, False otherwise
    """
    if set(state1.keys()) != set(state2.keys()):
        return False

    for key in state1:
        if state1[key] != state2[key]:
            return False

    return True


def validate_feedback_structure(feedback: dict[str, Any]) -> bool:
    """Validate feedback data structure.

    Args:
        feedback: Feedback dictionary

    Returns:
        True if feedback structure is valid, False otherwise
    """
    required_fields = ["score", "invocation_id"]
    for field in required_fields:
        if field not in feedback:
            return False

    # Validate score is numeric
    if not isinstance(feedback["score"], (int, float)):
        return False

    # Validate invocation_id is string
    if not isinstance(feedback["invocation_id"], str):
        return False

    return True


def count_tool_calls(events: list[dict[str, Any]]) -> dict[str, int]:
    """Count tool calls in events.

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary mapping tool names to call counts
    """
    tool_calls: dict[str, int] = {}

    for event in events:
        if "tool_call" in event:
            tool_name = event["tool_call"].get("name", "unknown")
            tool_calls[tool_name] = tool_calls.get(tool_name, 0) + 1

    return tool_calls


def measure_response_time(func: Callable[[], Any]) -> tuple[Any, float]:
    """Measure the execution time of a function.

    Args:
        func: Function to measure

    Returns:
        Tuple of (function result, execution time in seconds)
    """
    start_time = time.time()
    result = func()
    end_time = time.time()
    return result, end_time - start_time


def create_test_message(text: str, role: str = "user") -> Any:
    """Create a test message in the expected format.

    Args:
        text: Message text
        role: Message role (user or model)

    Returns:
        Message object
    """
    from google.genai import types

    return types.Content(role=role, parts=[types.Part.from_text(text=text)])


def filter_events_by_type(
    events: list[dict[str, Any]], event_type: str
) -> list[dict[str, Any]]:
    """Filter events by type.

    Args:
        events: List of event dictionaries
        event_type: Type of events to filter for

    Returns:
        Filtered list of events
    """
    return [event for event in events if event.get("type") == event_type]


def assert_no_errors_in_events(events: list[dict[str, Any]]) -> None:
    """Assert that no events contain errors.

    Args:
        events: List of event dictionaries

    Raises:
        AssertionError: If any event contains an error
    """
    for event in events:
        assert "error" not in event, f"Event contains error: {event.get('error')}"
        content = event.get("content")
        if content and hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "error") and part.error:
                    raise AssertionError(f"Part contains error: {part.error}")

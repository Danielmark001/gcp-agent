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

"""Main agent module with multi-agent system integration.

This module provides both:
1. A simple root agent for basic tasks (backward compatibility)
2. A multi-agent system for complex, coordinated tasks
"""

import datetime
import os
from zoneinfo import ZoneInfo

import google.auth

from app.agents.registry import get_agent_registry
from app.config.agent_config import get_agent_config

_, project_id = google.auth.default()
if project_id:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


# ============================================================================
# Simple utility tools (for backward compatibility and basic operations)
# ============================================================================


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# ============================================================================
# Multi-Agent System Setup
# ============================================================================

# Initialize agent configuration
agent_config = get_agent_config()

# Initialize agent registry and create multi-agent system
agent_registry = get_agent_registry(config=agent_config)

# Create the complete multi-agent system
# This sets up the coordinator and all specialized agents
coordinator_agent = agent_registry.create_multi_agent_system()

# For backward compatibility, create a simple root_agent with basic tools
# This maintains the original behavior while also providing multi-agent capabilities
from google.adk.agents import Agent as ADKAgent

root_agent = ADKAgent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[get_weather, get_current_time],
)


# ============================================================================
# Helper functions for accessing the multi-agent system
# ============================================================================


def get_coordinator() -> object:
    """Get the coordinator agent instance.

    Returns:
        The coordinator agent that orchestrates the multi-agent system.
    """
    return coordinator_agent


def get_specialized_agent(agent_name: str) -> object:
    """Get a specialized agent by name.

    Args:
        agent_name: Name of the agent to retrieve.

    Returns:
        The specialized agent instance or None if not found.
    """
    return agent_registry.get_agent(agent_name)


def get_all_agents() -> dict[str, object]:
    """Get all registered agents.

    Returns:
        Dictionary mapping agent names to agent instances.
    """
    return agent_registry.get_all_agents()


def get_agent_registry_instance() -> object:
    """Get the global agent registry instance.

    Returns:
        The agent registry managing all agents.
    """
    return agent_registry

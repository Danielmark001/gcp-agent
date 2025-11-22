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

"""State management for multi-agent coordination."""

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Represents the state of a single agent."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
    status: str = "idle"  # idle, working, completed, error
    current_task: str | None = None
    results: list[Any] = field(default_factory=list)


@dataclass
class Message:
    """Represents a message between agents."""

    from_agent: str
    to_agent: str
    content: dict[str, Any]
    timestamp: float = field(default_factory=lambda: __import__("time").time())


class StateManager:
    """Manages state and communication between agents in the multi-agent system.

    This class provides thread-safe state management, inter-agent messaging,
    and coordination capabilities.
    """

    def __init__(self) -> None:
        """Initialize the state manager."""
        self._states: dict[str, AgentState] = {}
        self._messages: dict[str, list[Message]] = defaultdict(list)
        self._lock = threading.RLock()
        self._global_context: dict[str, Any] = {}

    def register_agent(self, agent_name: str) -> None:
        """Register a new agent in the state manager.

        Args:
            agent_name: Name of the agent to register.
        """
        with self._lock:
            if agent_name not in self._states:
                self._states[agent_name] = AgentState(name=agent_name)

    def get_agent_state(self, agent_name: str) -> AgentState:
        """Get the state of a specific agent.

        Args:
            agent_name: Name of the agent.

        Returns:
            The AgentState object.
        """
        with self._lock:
            if agent_name not in self._states:
                self.register_agent(agent_name)
            return self._states[agent_name]

    def set(self, agent_name: str, key: str, value: Any) -> None:
        """Set a state value for an agent.

        Args:
            agent_name: Name of the agent.
            key: State key to set.
            value: Value to set.
        """
        with self._lock:
            state = self.get_agent_state(agent_name)
            state.data[key] = value

    def get(self, agent_name: str, key: str) -> Any:
        """Get a state value for an agent.

        Args:
            agent_name: Name of the agent.
            key: State key to get.

        Returns:
            The state value or None if not found.
        """
        with self._lock:
            state = self.get_agent_state(agent_name)
            return state.data.get(key)

    def update_status(
        self, agent_name: str, status: str, current_task: str | None = None
    ) -> None:
        """Update the status of an agent.

        Args:
            agent_name: Name of the agent.
            status: New status (idle, working, completed, error).
            current_task: Optional current task description.
        """
        with self._lock:
            state = self.get_agent_state(agent_name)
            state.status = status
            if current_task is not None:
                state.current_task = current_task

    def add_result(self, agent_name: str, result: Any) -> None:
        """Add a result to an agent's result list.

        Args:
            agent_name: Name of the agent.
            result: Result to add.
        """
        with self._lock:
            state = self.get_agent_state(agent_name)
            state.results.append(result)

    def send_message(
        self, from_agent: str, to_agent: str, content: dict[str, Any]
    ) -> None:
        """Send a message from one agent to another.

        Args:
            from_agent: Name of the sending agent.
            to_agent: Name of the receiving agent.
            content: Message content dictionary.
        """
        with self._lock:
            message = Message(from_agent=from_agent, to_agent=to_agent, content=content)
            self._messages[to_agent].append(message)

    def get_messages(self, agent_name: str, clear: bool = False) -> list[dict[str, Any]]:
        """Get messages for an agent.

        Args:
            agent_name: Name of the agent.
            clear: Whether to clear messages after reading.

        Returns:
            List of message dictionaries.
        """
        with self._lock:
            messages = [
                {
                    "from": msg.from_agent,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                }
                for msg in self._messages[agent_name]
            ]
            if clear:
                self._messages[agent_name].clear()
            return messages

    def set_global_context(self, key: str, value: Any) -> None:
        """Set a global context value accessible to all agents.

        Args:
            key: Context key.
            value: Context value.
        """
        with self._lock:
            self._global_context[key] = value

    def get_global_context(self, key: str) -> Any:
        """Get a global context value.

        Args:
            key: Context key.

        Returns:
            The context value or None if not found.
        """
        with self._lock:
            return self._global_context.get(key)

    def get_all_agent_states(self) -> dict[str, AgentState]:
        """Get states of all registered agents.

        Returns:
            Dictionary mapping agent names to their states.
        """
        with self._lock:
            return self._states.copy()

    def reset(self) -> None:
        """Reset all state and messages."""
        with self._lock:
            self._states.clear()
            self._messages.clear()
            self._global_context.clear()

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

"""Base agent class for specialized agents in the multi-agent system."""

from abc import ABC, abstractmethod
from typing import Any

from google.adk.agents import Agent

from app.agents.state_manager import AgentState, StateManager


class BaseSpecializedAgent(ABC):
    """Base class for all specialized agents in the system.

    Provides common functionality for agent initialization, state management,
    and communication with other agents.
    """

    def __init__(
        self,
        name: str,
        model: str = "gemini-2.0-flash",
        instruction: str = "",
        tools: list[Any] | None = None,
        state_manager: StateManager | None = None,
    ) -> None:
        """Initialize the base specialized agent.

        Args:
            name: Unique identifier for this agent.
            model: The model to use for this agent.
            instruction: System instruction for the agent.
            tools: List of tools available to this agent.
            state_manager: Optional state manager for coordination.
        """
        self.name = name
        self.model = model
        self.instruction = instruction
        self.tools = tools or []
        self.state_manager = state_manager or StateManager()
        self._agent: Agent | None = None

    @abstractmethod
    def get_system_instruction(self) -> str:
        """Get the system instruction for this agent.

        Returns:
            The system instruction string.
        """
        pass

    @abstractmethod
    def get_tools(self) -> list[Any]:
        """Get the list of tools for this agent.

        Returns:
            List of tool functions.
        """
        pass

    def create_agent(self) -> Agent:
        """Create and return the ADK Agent instance.

        Returns:
            Configured ADK Agent instance.
        """
        if self._agent is None:
            self._agent = Agent(
                name=self.name,
                model=self.model,
                instruction=self.get_system_instruction(),
                tools=self.get_tools(),
            )
        return self._agent

    def update_state(self, key: str, value: Any) -> None:
        """Update the shared state.

        Args:
            key: State key to update.
            value: Value to set.
        """
        self.state_manager.set(self.name, key, value)

    def get_state(self, agent_name: str, key: str) -> Any:
        """Get state from another agent or self.

        Args:
            agent_name: Name of the agent whose state to retrieve.
            key: State key to retrieve.

        Returns:
            The state value or None if not found.
        """
        return self.state_manager.get(agent_name, key)

    def get_agent_state(self) -> AgentState:
        """Get the current state of this agent.

        Returns:
            AgentState object containing this agent's state.
        """
        return self.state_manager.get_agent_state(self.name)

    def send_message(self, target_agent: str, message: dict[str, Any]) -> None:
        """Send a message to another agent via the state manager.

        Args:
            target_agent: Name of the target agent.
            message: Message dictionary to send.
        """
        self.state_manager.send_message(self.name, target_agent, message)

    def get_messages(self) -> list[dict[str, Any]]:
        """Get messages sent to this agent.

        Returns:
            List of message dictionaries.
        """
        return self.state_manager.get_messages(self.name)

    def execute_task(self, task: str, context: dict[str, Any] | None = None) -> str:
        """Execute a task using this agent.

        Args:
            task: The task description.
            context: Optional context dictionary.

        Returns:
            The agent's response.
        """
        self.create_agent()
        # Store context in state if provided
        if context:
            for key, value in context.items():
                self.update_state(key, value)

        # Execute the task (this would integrate with ADK's query method)
        # For now, we return a placeholder
        return f"Agent {self.name} executing task: {task}"

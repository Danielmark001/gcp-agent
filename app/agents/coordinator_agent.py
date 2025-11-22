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

"""Coordinator agent for orchestrating tasks across specialized agents."""

import json
from typing import Any

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.state_manager import StateManager
from app.config.agent_config import get_agent_config


class CoordinatorAgent(BaseSpecializedAgent):
    """Coordinator agent that orchestrates tasks across specialized agents.

    This agent analyzes incoming requests, determines which specialized agents
    are needed, delegates subtasks, and synthesizes results.
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        config: Any = None,
    ) -> None:
        """Initialize the coordinator agent.

        Args:
            state_manager: Optional state manager for coordination.
            config: Optional configuration object.
        """
        self.config = config or get_agent_config()
        super().__init__(
            name=self.config.coordinator_name,
            model=self.config.coordinator_model,
            state_manager=state_manager,
        )
        self.available_agents: dict[str, str] = {}

    def register_specialized_agent(self, agent_name: str, description: str) -> None:
        """Register a specialized agent with the coordinator.

        Args:
            agent_name: Name of the agent to register.
            description: Description of the agent's capabilities.
        """
        self.available_agents[agent_name] = description
        self.state_manager.register_agent(agent_name)

    def get_system_instruction(self) -> str:
        """Get the system instruction for the coordinator agent.

        Returns:
            The system instruction string.
        """
        agents_info = "\n".join(
            [f"- {name}: {desc}" for name, desc in self.available_agents.items()]
        )

        return f"""You are the Coordinator Agent in a multi-agent system. Your role is to:

1. Analyze incoming user requests
2. Determine which specialized agents are needed
3. Break down complex tasks into subtasks
4. Delegate subtasks to appropriate specialized agents
5. Monitor task progress and agent status
6. Synthesize results from multiple agents
7. Handle errors and retries

Available specialized agents:
{agents_info}

When you receive a request, analyze it carefully and determine which agents should handle it.
You can delegate tasks to multiple agents in parallel if they are independent.
Always provide clear, structured instructions to each agent."""

    def get_tools(self) -> list[Any]:
        """Get the list of tools for the coordinator agent.

        Returns:
            List of tool functions.
        """

        def delegate_task(agent_name: str, task: str, context: str = "") -> str:
            """Delegate a task to a specialized agent.

            Args:
                agent_name: Name of the agent to delegate to.
                task: Description of the task to perform.
                context: Additional context for the task.

            Returns:
                Confirmation message with task ID.
            """
            if agent_name not in self.available_agents:
                return f"Error: Agent '{agent_name}' not found. Available agents: {', '.join(self.available_agents.keys())}"

            # Send task to the agent via state manager
            message = {
                "type": "task_delegation",
                "task": task,
                "context": context,
            }
            self.send_message(agent_name, message)
            self.state_manager.update_status(agent_name, "working", task)

            return f"Task delegated to {agent_name}: {task}"

        def get_agent_status(agent_name: str) -> str:
            """Get the current status of an agent.

            Args:
                agent_name: Name of the agent to check.

            Returns:
                Status information as JSON string.
            """
            if agent_name not in self.available_agents:
                return json.dumps(
                    {"error": f"Agent '{agent_name}' not found"},
                    indent=2,
                )

            state = self.state_manager.get_agent_state(agent_name)
            return json.dumps(
                {
                    "agent": agent_name,
                    "status": state.status,
                    "current_task": state.current_task,
                    "results_count": len(state.results),
                },
                indent=2,
            )

        def get_agent_results(agent_name: str) -> str:
            """Get the results from a specific agent.

            Args:
                agent_name: Name of the agent.

            Returns:
                Results as JSON string.
            """
            if agent_name not in self.available_agents:
                return json.dumps(
                    {"error": f"Agent '{agent_name}' not found"},
                    indent=2,
                )

            state = self.state_manager.get_agent_state(agent_name)
            return json.dumps(
                {
                    "agent": agent_name,
                    "results": state.results,
                },
                indent=2,
            )

        def get_all_agents_status() -> str:
            """Get the status of all registered agents.

            Returns:
                Status information for all agents as JSON string.
            """
            all_states = self.state_manager.get_all_agent_states()
            status_info = {
                name: {
                    "status": state.status,
                    "current_task": state.current_task,
                    "results_count": len(state.results),
                }
                for name, state in all_states.items()
            }
            return json.dumps(status_info, indent=2)

        def synthesize_results(agent_names: str, synthesis_prompt: str) -> str:
            """Synthesize results from multiple agents.

            Args:
                agent_names: Comma-separated list of agent names.
                synthesis_prompt: How to synthesize the results.

            Returns:
                Synthesized results.
            """
            agents = [name.strip() for name in agent_names.split(",")]
            results = {}

            for agent_name in agents:
                if agent_name in self.available_agents:
                    state = self.state_manager.get_agent_state(agent_name)
                    results[agent_name] = state.results

            return json.dumps(
                {
                    "synthesis_prompt": synthesis_prompt,
                    "agent_results": results,
                    "note": "Use this information to create your final response",
                },
                indent=2,
            )

        return [
            delegate_task,
            get_agent_status,
            get_agent_results,
            get_all_agents_status,
            synthesize_results,
        ]

    def orchestrate(
        self, user_query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Orchestrate task execution across specialized agents.

        Args:
            user_query: The user's query or request.
            context: Optional context dictionary.

        Returns:
            Dictionary with orchestration results.
        """
        # Store the query in global context
        self.state_manager.set_global_context("user_query", user_query)
        if context:
            for key, value in context.items():
                self.state_manager.set_global_context(key, value)

        # Update coordinator status
        self.update_state("status", "orchestrating")
        self.update_state("query", user_query)

        return {
            "status": "orchestration_initiated",
            "query": user_query,
            "available_agents": list(self.available_agents.keys()),
            "message": "Coordinator agent initialized and ready to delegate tasks",
        }

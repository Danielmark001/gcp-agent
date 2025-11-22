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

"""Agent registry and factory for creating and managing specialized agents."""

from typing import Any, ClassVar

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.code_generation_agent import CodeGenerationAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.data_analysis_agent import DataAnalysisAgent
from app.agents.research_agent import ResearchAgent
from app.agents.state_manager import StateManager
from app.config.agent_config import AgentConfig, get_agent_config


class AgentRegistry:
    """Registry for managing and creating specialized agents.

    Implements the Factory pattern for agent creation and provides
    centralized agent management.
    """

    # Agent type constants
    COORDINATOR = "coordinator"
    RESEARCH = "research"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"

    # Agent type to class mapping
    _AGENT_CLASSES: ClassVar[dict[str, type[BaseSpecializedAgent]]] = {
        COORDINATOR: CoordinatorAgent,
        RESEARCH: ResearchAgent,
        CODE_GENERATION: CodeGenerationAgent,
        DATA_ANALYSIS: DataAnalysisAgent,
    }

    # Agent descriptions for coordinator registration
    _AGENT_DESCRIPTIONS: ClassVar[dict[str, str]] = {
        RESEARCH: "Specialized in gathering information, conducting web searches, "
        "and synthesizing research findings. Use for information gathering, "
        "fact-checking, and research tasks.",
        CODE_GENERATION: "Specialized in generating, reviewing, and refactoring code "
        "in multiple programming languages. Use for code writing, "
        "code review, test generation, and technical documentation.",
        DATA_ANALYSIS: "Specialized in analyzing datasets, performing statistical analysis, "
        "identifying patterns, and generating visualizations. Use for data "
        "processing, insights generation, and analytical reports.",
    }

    def __init__(
        self, config: AgentConfig | None = None, state_manager: StateManager | None = None
    ) -> None:
        """Initialize the agent registry.

        Args:
            config: Optional configuration for agents.
            state_manager: Optional shared state manager.
        """
        self.config = config or get_agent_config()
        self.state_manager = state_manager or StateManager()
        self._agents: dict[str, BaseSpecializedAgent] = {}

    def create_agent(
        self, agent_type: str, **kwargs: Any
    ) -> BaseSpecializedAgent:
        """Create a new agent of the specified type.

        Args:
            agent_type: Type of agent to create (use class constants).
            **kwargs: Additional arguments to pass to agent constructor.

        Returns:
            Created agent instance.

        Raises:
            ValueError: If agent_type is not recognized.
        """
        if agent_type not in self._AGENT_CLASSES:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available types: {', '.join(self._AGENT_CLASSES.keys())}"
            )

        agent_class = self._AGENT_CLASSES[agent_type]

        # Merge default kwargs with provided ones
        agent_kwargs = {
            "state_manager": self.state_manager,
            "config": self.config,
            **kwargs,
        }

        agent = agent_class(**agent_kwargs)

        # Register agent in state manager
        self.state_manager.register_agent(agent.name)

        # Cache the agent
        self._agents[agent.name] = agent

        return agent

    def get_agent(self, agent_name: str) -> BaseSpecializedAgent | None:
        """Get an agent by name.

        Args:
            agent_name: Name of the agent to retrieve.

        Returns:
            The agent instance or None if not found.
        """
        return self._agents.get(agent_name)

    def get_all_agents(self) -> dict[str, BaseSpecializedAgent]:
        """Get all registered agents.

        Returns:
            Dictionary mapping agent names to agent instances.
        """
        return self._agents.copy()

    def register_agent(self, agent: BaseSpecializedAgent) -> None:
        """Register an existing agent instance.

        Args:
            agent: Agent instance to register.
        """
        self._agents[agent.name] = agent
        self.state_manager.register_agent(agent.name)

    def create_multi_agent_system(self) -> CoordinatorAgent:
        """Create a complete multi-agent system with all specialized agents.

        Returns:
            Coordinator agent that orchestrates the system.
        """
        # Create coordinator agent
        coordinator = self.create_agent(self.COORDINATOR)

        # Create specialized agents
        research_agent = self.create_agent(self.RESEARCH)
        code_gen_agent = self.create_agent(self.CODE_GENERATION)
        data_analysis_agent = self.create_agent(self.DATA_ANALYSIS)

        # Register specialized agents with coordinator
        if isinstance(coordinator, CoordinatorAgent):
            coordinator.register_specialized_agent(
                research_agent.name, self._AGENT_DESCRIPTIONS[self.RESEARCH]
            )
            coordinator.register_specialized_agent(
                code_gen_agent.name, self._AGENT_DESCRIPTIONS[self.CODE_GENERATION]
            )
            coordinator.register_specialized_agent(
                data_analysis_agent.name, self._AGENT_DESCRIPTIONS[self.DATA_ANALYSIS]
            )

        return coordinator

    def get_agent_types(self) -> list[str]:
        """Get list of available agent types.

        Returns:
            List of agent type identifiers.
        """
        return list(self._AGENT_CLASSES.keys())

    def get_agent_description(self, agent_type: str) -> str:
        """Get description of an agent type.

        Args:
            agent_type: Type of agent.

        Returns:
            Description of the agent's capabilities.

        Raises:
            ValueError: If agent_type is not recognized.
        """
        if agent_type == self.COORDINATOR:
            return (
                "Orchestrates tasks across specialized agents, "
                "delegates work, and synthesizes results."
            )
        if agent_type in self._AGENT_DESCRIPTIONS:
            return self._AGENT_DESCRIPTIONS[agent_type]
        raise ValueError(f"Unknown agent type: {agent_type}")

    def reset_all_agents(self) -> None:
        """Reset all agents and clear the registry."""
        self._agents.clear()
        self.state_manager.reset()


# Global registry instance
_global_registry: AgentRegistry | None = None


def get_agent_registry(
    config: AgentConfig | None = None, state_manager: StateManager | None = None
) -> AgentRegistry:
    """Get the global agent registry.

    Args:
        config: Optional configuration for agents.
        state_manager: Optional shared state manager.

    Returns:
        The global AgentRegistry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry(config=config, state_manager=state_manager)
    return _global_registry


def reset_agent_registry() -> None:
    """Reset the global agent registry."""
    global _global_registry
    if _global_registry is not None:
        _global_registry.reset_all_agents()
    _global_registry = None

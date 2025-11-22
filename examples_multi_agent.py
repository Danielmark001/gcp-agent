#!/usr/bin/env python3
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

"""Example usage of the multi-agent system.

This script demonstrates how to use the multi-agent system for various tasks.
"""

import json

from app.agent import (
    get_agent_registry_instance,
    get_all_agents,
    get_coordinator,
    get_specialized_agent,
)
from app.agents.registry import AgentRegistry
from app.config.agent_config import AgentConfig


def example_1_basic_usage() -> None:
    """Example 1: Basic usage with the coordinator agent."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Coordinator Usage")
    print("=" * 80)

    # Get the coordinator
    coordinator = get_coordinator()

    # Orchestrate a simple task
    result = coordinator.orchestrate(
        user_query="What are the best practices for Python development?",
        context={"language": "python", "focus": "best_practices"},
    )

    print("\nOrchestration Result:")
    print(json.dumps(result, indent=2))


def example_2_research_agent() -> None:
    """Example 2: Using the research agent directly."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Research Agent Direct Usage")
    print("=" * 80)

    # Get the research agent
    research_agent = get_specialized_agent("research_agent")

    if research_agent:
        # Create ADK agent and get tools
        adk_agent = research_agent.create_agent()
        tools = research_agent.get_tools()

        print(f"\nResearch Agent: {research_agent.name}")
        print(f"Available Tools: {len(tools)}")

        # Use a tool
        web_search_tool = tools[0]  # web_search
        search_result = web_search_tool("machine learning frameworks", 3)

        print("\nSearch Results:")
        print(search_result)


def example_3_code_generation() -> None:
    """Example 3: Using the code generation agent."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Code Generation Agent Usage")
    print("=" * 80)

    # Get the code generation agent
    code_agent = get_specialized_agent("code_generation_agent")

    if code_agent:
        # Create ADK agent and get tools
        adk_agent = code_agent.create_agent()
        tools = code_agent.get_tools()

        print(f"\nCode Generation Agent: {code_agent.name}")
        print(f"Available Tools: {len(tools)}")

        # Use the generate_code tool
        generate_code_tool = tools[0]
        code_result = generate_code_tool(
            "python",
            "A function to validate email addresses",
            "Use regex pattern matching",
        )

        print("\nGenerated Code:")
        print(code_result)


def example_4_data_analysis() -> None:
    """Example 4: Using the data analysis agent."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Data Analysis Agent Usage")
    print("=" * 80)

    # Get the data analysis agent
    data_agent = get_specialized_agent("data_analysis_agent")

    if data_agent:
        # Create ADK agent and get tools
        adk_agent = data_agent.create_agent()
        tools = data_agent.get_tools()

        print(f"\nData Analysis Agent: {data_agent.name}")
        print(f"Available Tools: {len(tools)}")

        # Use the analyze_dataset tool
        analyze_tool = tools[0]
        analysis_result = analyze_tool(
            "Sales data for Q4 2024", "trend", "revenue,quantity,region"
        )

        print("\nAnalysis Results:")
        print(analysis_result)


def example_5_agent_coordination() -> None:
    """Example 5: Coordinating multiple agents."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Multi-Agent Coordination")
    print("=" * 80)

    # Get the coordinator
    coordinator = get_coordinator()

    # Get coordinator tools
    tools = coordinator.get_tools()

    print(f"\nCoordinator Tools: {len(tools)}")

    # Delegate task to research agent
    delegate_tool = tools[0]  # delegate_task
    print("\n--- Delegating research task ---")
    result1 = delegate_tool(
        "research_agent",
        "Research current trends in AI and machine learning",
        "Focus on 2024-2025 developments",
    )
    print(result1)

    # Delegate task to code generation agent
    print("\n--- Delegating code generation task ---")
    result2 = delegate_tool(
        "code_generation_agent",
        "Generate a Python class for data processing",
        "Include error handling and type hints",
    )
    print(result2)

    # Check all agent statuses
    get_all_status_tool = tools[3]  # get_all_agents_status
    print("\n--- All Agent Statuses ---")
    statuses = get_all_status_tool()
    print(statuses)


def example_6_custom_configuration() -> None:
    """Example 6: Creating agents with custom configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Custom Configuration")
    print("=" * 80)

    # Create custom configuration
    custom_config = AgentConfig(
        default_model="gemini-2.0-flash",
        max_iterations=20,
        timeout_seconds=600,
        research_max_search_results=15,
        code_gen_supported_languages=["python", "javascript", "go"],
    )

    print("\nCustom Configuration:")
    print(json.dumps(custom_config.to_dict(), indent=2))

    # Note: In production, you would use this config to create a new registry
    # For this example, we'll just display the configuration


def example_7_state_management() -> None:
    """Example 7: Working with state management."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: State Management")
    print("=" * 80)

    # Get the registry and state manager
    registry = get_agent_registry_instance()
    state_manager = registry.state_manager

    # Set some global context
    state_manager.set_global_context("project_name", "Multi-Agent Example")
    state_manager.set_global_context("version", "1.0.0")

    # Get an agent and update its state
    research_agent = get_specialized_agent("research_agent")
    if research_agent:
        research_agent.update_state("current_focus", "AI trends")
        research_agent.update_state("tasks_completed", 0)

    # Retrieve state
    project_name = state_manager.get_global_context("project_name")
    print(f"\nProject Name: {project_name}")

    # Get all agent states
    all_states = state_manager.get_all_agent_states()
    print(f"\nRegistered Agents: {len(all_states)}")
    for name, state in all_states.items():
        print(f"  - {name}: {state.status}")


def example_8_registry_operations() -> None:
    """Example 8: Working with the agent registry."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Agent Registry Operations")
    print("=" * 80)

    registry = get_agent_registry_instance()

    # Get all agents
    all_agents = get_all_agents()
    print(f"\nTotal Registered Agents: {len(all_agents)}")

    for name, agent in all_agents.items():
        print(f"\n  Agent: {name}")
        print(f"  Model: {agent.model}")
        print(f"  Tools: {len(agent.get_tools())}")

    # Get available agent types
    agent_types = registry.get_agent_types()
    print(f"\nAvailable Agent Types: {agent_types}")

    # Get agent descriptions
    for agent_type in agent_types:
        try:
            description = registry.get_agent_description(agent_type)
            print(f"\n{agent_type.upper()}:")
            print(f"  {description}")
        except ValueError:
            pass


def main() -> None:
    """Run all examples."""
    print("\n" + "#" * 80)
    print("# Multi-Agent System Examples")
    print("#" * 80)

    # Run examples
    example_1_basic_usage()
    example_2_research_agent()
    example_3_code_generation()
    example_4_data_analysis()
    example_5_agent_coordination()
    example_6_custom_configuration()
    example_7_state_management()
    example_8_registry_operations()

    print("\n" + "#" * 80)
    print("# Examples Complete")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()

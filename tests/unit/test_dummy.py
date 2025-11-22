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
"""
Unit tests for agent configuration and basic functionality.
"""

from app.agent import root_agent


class TestAgentConfiguration:
    """Tests for agent configuration."""

    def test_agent_exists(self) -> None:
        """Test that root agent is configured."""
        assert root_agent is not None

    def test_agent_has_name(self) -> None:
        """Test that agent has a name."""
        assert root_agent.name == "root_agent"

    def test_agent_has_model(self) -> None:
        """Test that agent has a model configured."""
        assert root_agent.model == "gemini-2.0-flash"

    def test_agent_has_instruction(self) -> None:
        """Test that agent has an instruction."""
        assert root_agent.instruction is not None
        assert len(root_agent.instruction) > 0
        assert "helpful" in root_agent.instruction.lower()

    def test_agent_has_tools(self) -> None:
        """Test that agent has tools configured."""
        assert root_agent.tools is not None
        assert len(root_agent.tools) == 2  # get_weather and get_current_time

    def test_agent_tool_names(self) -> None:
        """Test that agent has the expected tools."""
        tool_names = [tool.__name__ for tool in root_agent.tools]
        assert "get_weather" in tool_names
        assert "get_current_time" in tool_names

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

"""Research agent for gathering information and conducting web searches."""

import json
from typing import Any
from urllib.parse import quote_plus

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.state_manager import StateManager
from app.config.agent_config import get_agent_config


class ResearchAgent(BaseSpecializedAgent):
    """Research agent specialized in gathering information and conducting research.

    This agent can search the web, gather information from various sources,
    and synthesize research findings.
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        config: Any = None,
    ) -> None:
        """Initialize the research agent.

        Args:
            state_manager: Optional state manager for coordination.
            config: Optional configuration object.
        """
        self.config = config or get_agent_config()
        super().__init__(
            name=self.config.research_name,
            model=self.config.research_model,
            state_manager=state_manager,
        )

    def get_system_instruction(self) -> str:
        """Get the system instruction for the research agent.

        Returns:
            The system instruction string.
        """
        return """You are the Research Agent in a multi-agent system. Your role is to:

1. Conduct thorough research on topics and questions
2. Search for relevant information from various sources
3. Gather and organize factual information
4. Validate information accuracy when possible
5. Synthesize research findings into coherent summaries
6. Provide citations and sources for information

When conducting research:
- Use search tools to find relevant information
- Cross-reference information from multiple sources
- Distinguish between facts, opinions, and speculation
- Provide clear, well-organized research summaries
- Include sources and references in your findings

Your research should be comprehensive, accurate, and well-documented."""

    def get_tools(self) -> list[Any]:
        """Get the list of tools for the research agent.

        Returns:
            List of tool functions.
        """

        def web_search(query: str, num_results: int = 5) -> str:
            """Simulate a web search for information.

            Args:
                query: The search query.
                num_results: Number of results to return (default 5).

            Returns:
                Search results as JSON string.
            """
            # This is a simulated search - in production, integrate with actual search API
            self.update_state("last_search_query", query)
            self.state_manager.add_result(
                self.name,
                {
                    "type": "search",
                    "query": query,
                    "num_results": num_results,
                },
            )

            # Simulate search results
            results = {
                "query": query,
                "results": [
                    {
                        "title": f"Result {i + 1} for: {query}",
                        "url": f"https://example.com/result{i + 1}?q={quote_plus(query)}",
                        "snippet": f"This is a simulated search result snippet for query: {query}. "
                        f"Result number {i + 1} contains relevant information.",
                    }
                    for i in range(min(num_results, self.config.research_max_search_results))
                ],
                "note": "These are simulated results. In production, integrate with Google Search API or similar.",
            }

            return json.dumps(results, indent=2)

        def gather_information(topic: str, sources: str = "") -> str:
            """Gather comprehensive information on a topic.

            Args:
                topic: The topic to research.
                sources: Optional comma-separated list of sources to focus on.

            Returns:
                Gathered information as JSON string.
            """
            self.update_state("current_research_topic", topic)
            self.state_manager.add_result(
                self.name,
                {
                    "type": "information_gathering",
                    "topic": topic,
                    "sources": sources,
                },
            )

            source_list = [s.strip() for s in sources.split(",")] if sources else ["general"]

            info = {
                "topic": topic,
                "sources": source_list,
                "information": {
                    "overview": f"Comprehensive information about {topic}",
                    "key_points": [
                        f"Key point 1 about {topic}",
                        f"Key point 2 about {topic}",
                        f"Key point 3 about {topic}",
                    ],
                    "details": f"Detailed information about {topic} gathered from sources: {', '.join(source_list)}",
                },
                "note": "This is simulated information gathering. Integrate with real data sources in production.",
            }

            return json.dumps(info, indent=2)

        def verify_information(claim: str, sources: str = "") -> str:
            """Verify a claim or piece of information.

            Args:
                claim: The claim to verify.
                sources: Optional comma-separated list of sources to check.

            Returns:
                Verification result as JSON string.
            """
            self.state_manager.add_result(
                self.name,
                {
                    "type": "verification",
                    "claim": claim,
                    "sources": sources,
                },
            )

            result = {
                "claim": claim,
                "verification_status": "pending",
                "confidence": "medium",
                "sources_checked": sources.split(",") if sources else ["general"],
                "findings": f"Verification findings for: {claim}",
                "note": "This is a simulated verification. Implement actual fact-checking in production.",
            }

            return json.dumps(result, indent=2)

        def synthesize_research(topic: str, key_points: str) -> str:
            """Synthesize research findings into a summary.

            Args:
                topic: The research topic.
                key_points: Comma-separated list of key points to include.

            Returns:
                Research synthesis as JSON string.
            """
            points = [p.strip() for p in key_points.split(",")]

            synthesis = {
                "topic": topic,
                "key_findings": points,
                "summary": f"Research summary for {topic} covering: {', '.join(points)}",
                "recommendations": [
                    "Recommendation 1 based on research",
                    "Recommendation 2 based on research",
                ],
                "sources": ["Source 1", "Source 2", "Source 3"],
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "synthesis",
                    "topic": topic,
                    "synthesis": synthesis,
                },
            )

            return json.dumps(synthesis, indent=2)

        def get_current_knowledge(topic: str) -> str:
            """Get current knowledge and understanding about a topic.

            Args:
                topic: The topic to get knowledge about.

            Returns:
                Current knowledge as JSON string.
            """
            knowledge = {
                "topic": topic,
                "status": "Using AI knowledge base",
                "coverage": "general",
                "last_updated": "2025-01",
                "note": f"Information about {topic} from AI knowledge base. "
                "For real-time information, use web_search tool.",
            }

            return json.dumps(knowledge, indent=2)

        return [
            web_search,
            gather_information,
            verify_information,
            synthesize_research,
            get_current_knowledge,
        ]

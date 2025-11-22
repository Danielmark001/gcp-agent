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

"""Code generation agent for writing and reviewing code."""

import json
from typing import Any

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.state_manager import StateManager
from app.config.agent_config import get_agent_config


class CodeGenerationAgent(BaseSpecializedAgent):
    """Code generation agent specialized in writing and reviewing code.

    This agent can generate code in various programming languages,
    review code for quality and security, and suggest improvements.
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        config: Any = None,
    ) -> None:
        """Initialize the code generation agent.

        Args:
            state_manager: Optional state manager for coordination.
            config: Optional configuration object.
        """
        self.config = config or get_agent_config()
        super().__init__(
            name=self.config.code_gen_name,
            model=self.config.code_gen_model,
            state_manager=state_manager,
        )

    def get_system_instruction(self) -> str:
        """Get the system instruction for the code generation agent.

        Returns:
            The system instruction string.
        """
        supported_languages = ", ".join(self.config.code_gen_supported_languages)

        return f"""You are the Code Generation Agent in a multi-agent system. Your role is to:

1. Generate high-quality code based on requirements
2. Write clean, maintainable, and well-documented code
3. Review code for quality, security, and best practices
4. Suggest code improvements and optimizations
5. Create unit tests and documentation
6. Debug and fix code issues

Supported programming languages: {supported_languages}

When generating code:
- Follow language-specific best practices and conventions
- Write clear comments and documentation
- Include error handling and input validation
- Consider performance and security implications
- Provide usage examples when appropriate
- Generate unit tests when requested

Your code should be production-ready and follow industry standards."""

    def get_tools(self) -> list[Any]:
        """Get the list of tools for the code generation agent.

        Returns:
            List of tool functions.
        """

        def generate_code(
            language: str, description: str, requirements: str = ""
        ) -> str:
            """Generate code based on requirements.

            Args:
                language: Programming language (e.g., python, javascript).
                description: Description of what the code should do.
                requirements: Optional specific requirements.

            Returns:
                Generated code with documentation as JSON string.
            """
            if language.lower() not in [
                lang.lower() for lang in self.config.code_gen_supported_languages
            ]:
                return json.dumps(
                    {
                        "error": f"Language '{language}' not supported. "
                        f"Supported: {', '.join(self.config.code_gen_supported_languages)}"
                    },
                    indent=2,
                )

            self.update_state("last_generated_language", language)
            self.state_manager.add_result(
                self.name,
                {
                    "type": "code_generation",
                    "language": language,
                    "description": description,
                },
            )

            # Simulate code generation
            code_result = {
                "language": language,
                "description": description,
                "requirements": requirements,
                "code": f"# Generated {language} code for: {description}\n"
                f"# Requirements: {requirements}\n\n"
                "def example_function():\n"
                '    """Example function generated based on requirements."""\n'
                "    pass\n",
                "documentation": f"Documentation for {language} code implementing: {description}",
                "usage_example": "# Usage:\n# example_function()\n",
                "note": "This is simulated code generation. Implement actual code generation logic.",
            }

            return json.dumps(code_result, indent=2)

        def review_code(code: str, language: str, focus_areas: str = "") -> str:
            """Review code for quality, security, and best practices.

            Args:
                code: The code to review.
                language: Programming language of the code.
                focus_areas: Optional comma-separated focus areas (e.g., security, performance).

            Returns:
                Code review results as JSON string.
            """
            areas = [a.strip() for a in focus_areas.split(",")] if focus_areas else ["general"]

            review_result = {
                "language": language,
                "focus_areas": areas,
                "issues": [
                    {
                        "severity": "medium",
                        "type": "code_style",
                        "message": "Consider adding type hints for better code clarity",
                        "line": 1,
                    },
                    {
                        "severity": "low",
                        "type": "documentation",
                        "message": "Add docstring with parameter descriptions",
                        "line": 1,
                    },
                ],
                "suggestions": [
                    "Add error handling for edge cases",
                    "Consider extracting complex logic into separate functions",
                    "Add unit tests for critical functionality",
                ],
                "overall_score": 7.5,
                "note": "This is a simulated code review. Implement actual static analysis.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "code_review",
                    "language": language,
                    "review": review_result,
                },
            )

            return json.dumps(review_result, indent=2)

        def generate_tests(
            code: str, language: str, test_framework: str = ""
        ) -> str:
            """Generate unit tests for code.

            Args:
                code: The code to generate tests for.
                language: Programming language of the code.
                test_framework: Optional test framework (e.g., pytest, jest).

            Returns:
                Generated tests as JSON string.
            """
            framework = test_framework or (
                "pytest" if language.lower() == "python" else "default"
            )

            test_result = {
                "language": language,
                "test_framework": framework,
                "tests": f"# Unit tests using {framework}\n\n"
                "def test_example():\n"
                '    """Test example functionality."""\n'
                "    assert True\n\n"
                "def test_edge_cases():\n"
                '    """Test edge cases."""\n'
                "    assert True\n",
                "test_coverage": "85%",
                "test_cases": [
                    "Test normal input",
                    "Test edge cases",
                    "Test error handling",
                ],
                "note": "This is simulated test generation. Implement actual test generation logic.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "test_generation",
                    "language": language,
                    "framework": framework,
                },
            )

            return json.dumps(test_result, indent=2)

        def refactor_code(code: str, language: str, goals: str = "") -> str:
            """Refactor code for improved quality and maintainability.

            Args:
                code: The code to refactor.
                language: Programming language of the code.
                goals: Optional refactoring goals (e.g., performance, readability).

            Returns:
                Refactored code with explanation as JSON string.
            """
            refactor_goals = [g.strip() for g in goals.split(",")] if goals else ["general improvement"]

            refactor_result = {
                "language": language,
                "goals": refactor_goals,
                "original_code_length": len(code),
                "refactored_code": f"# Refactored {language} code\n"
                f"# Goals: {', '.join(refactor_goals)}\n\n"
                "def refactored_example():\n"
                '    """Improved and refactored function."""\n'
                "    pass\n",
                "improvements": [
                    "Improved code organization",
                    "Enhanced readability",
                    "Better error handling",
                    "Reduced complexity",
                ],
                "changes_summary": "Code refactored to improve " + ", ".join(refactor_goals),
                "note": "This is simulated refactoring. Implement actual refactoring logic.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "code_refactoring",
                    "language": language,
                    "goals": refactor_goals,
                },
            )

            return json.dumps(refactor_result, indent=2)

        def explain_code(code: str, language: str, detail_level: str = "medium") -> str:
            """Explain what code does in natural language.

            Args:
                code: The code to explain.
                language: Programming language of the code.
                detail_level: Level of detail (low, medium, high).

            Returns:
                Code explanation as JSON string.
            """
            explanation = {
                "language": language,
                "detail_level": detail_level,
                "summary": "This code performs specific functionality",
                "detailed_explanation": f"Detailed explanation of the {language} code at {detail_level} detail level",
                "key_components": [
                    "Component 1: Purpose and functionality",
                    "Component 2: Purpose and functionality",
                ],
                "note": "This is simulated code explanation. Implement actual code analysis.",
            }

            return json.dumps(explanation, indent=2)

        return [
            generate_code,
            review_code,
            generate_tests,
            refactor_code,
            explain_code,
        ]

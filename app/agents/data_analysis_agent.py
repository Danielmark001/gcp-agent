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

"""Data analysis agent for processing and analyzing data."""

import json
from typing import Any

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.state_manager import StateManager
from app.config.agent_config import get_agent_config


class DataAnalysisAgent(BaseSpecializedAgent):
    """Data analysis agent specialized in processing and analyzing data.

    This agent can analyze datasets, generate insights, create visualizations,
    and perform statistical analysis.
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        config: Any = None,
    ) -> None:
        """Initialize the data analysis agent.

        Args:
            state_manager: Optional state manager for coordination.
            config: Optional configuration object.
        """
        self.config = config or get_agent_config()
        super().__init__(
            name=self.config.data_analysis_name,
            model=self.config.data_analysis_model,
            state_manager=state_manager,
        )

    def get_system_instruction(self) -> str:
        """Get the system instruction for the data analysis agent.

        Returns:
            The system instruction string.
        """
        supported_formats = ", ".join(self.config.data_analysis_supported_formats)

        return f"""You are the Data Analysis Agent in a multi-agent system. Your role is to:

1. Analyze datasets and extract insights
2. Perform statistical analysis and calculations
3. Identify patterns, trends, and anomalies
4. Generate data visualizations and reports
5. Clean and preprocess data
6. Make data-driven recommendations

Supported data formats: {supported_formats}

When analyzing data:
- Validate data quality and integrity
- Use appropriate statistical methods
- Identify outliers and anomalies
- Generate clear, actionable insights
- Create meaningful visualizations
- Provide confidence levels and error margins

Your analysis should be rigorous, accurate, and well-documented."""

    def get_tools(self) -> list[Any]:
        """Get the list of tools for the data analysis agent.

        Returns:
            List of tool functions.
        """

        def analyze_dataset(
            data_description: str, analysis_type: str = "general", columns: str = ""
        ) -> str:
            """Analyze a dataset and generate insights.

            Args:
                data_description: Description of the dataset.
                analysis_type: Type of analysis (general, statistical, trend, etc.).
                columns: Optional comma-separated list of columns to focus on.

            Returns:
                Analysis results as JSON string.
            """
            cols = [c.strip() for c in columns.split(",")] if columns else ["all"]

            analysis_result = {
                "dataset": data_description,
                "analysis_type": analysis_type,
                "columns_analyzed": cols,
                "summary_statistics": {
                    "total_records": 1000,
                    "columns": len(cols),
                    "data_quality_score": 0.92,
                },
                "key_insights": [
                    f"Insight 1: {analysis_type} analysis reveals pattern in data",
                    f"Insight 2: Trend identified across {', '.join(cols[:3])}",
                    "Insight 3: Data quality is good with minimal missing values",
                ],
                "recommendations": [
                    "Recommendation 1 based on analysis",
                    "Recommendation 2 for data improvement",
                ],
                "note": "This is simulated data analysis. Integrate with actual data processing libraries.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "dataset_analysis",
                    "dataset": data_description,
                    "analysis_type": analysis_type,
                },
            )

            return json.dumps(analysis_result, indent=2)

        def perform_statistical_analysis(
            data_description: str, tests: str = "", confidence_level: float = 0.95
        ) -> str:
            """Perform statistical analysis on data.

            Args:
                data_description: Description of the data to analyze.
                tests: Comma-separated list of statistical tests to perform.
                confidence_level: Confidence level for statistical tests (default 0.95).

            Returns:
                Statistical analysis results as JSON string.
            """
            test_list = [t.strip() for t in tests.split(",")] if tests else ["descriptive"]

            stats_result = {
                "data": data_description,
                "tests_performed": test_list,
                "confidence_level": confidence_level,
                "results": {
                    "mean": 50.5,
                    "median": 48.2,
                    "std_dev": 12.3,
                    "min": 10.0,
                    "max": 95.0,
                    "p_value": 0.023,
                },
                "interpretation": f"Statistical analysis using {', '.join(test_list)} at {confidence_level} confidence",
                "significant_findings": [
                    "Finding 1: Statistically significant result",
                    "Finding 2: Notable pattern in distribution",
                ],
                "note": "This is simulated statistical analysis. Implement with scipy/statsmodels.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "statistical_analysis",
                    "tests": test_list,
                    "confidence_level": confidence_level,
                },
            )

            return json.dumps(stats_result, indent=2)

        def identify_patterns(
            data_description: str, pattern_type: str = "general"
        ) -> str:
            """Identify patterns and trends in data.

            Args:
                data_description: Description of the data.
                pattern_type: Type of pattern to look for (temporal, spatial, correlation, etc.).

            Returns:
                Pattern identification results as JSON string.
            """
            patterns_result = {
                "data": data_description,
                "pattern_type": pattern_type,
                "patterns_found": [
                    {
                        "pattern": "Increasing trend",
                        "strength": "strong",
                        "confidence": 0.87,
                        "description": f"{pattern_type} pattern showing consistent increase",
                    },
                    {
                        "pattern": "Seasonal variation",
                        "strength": "medium",
                        "confidence": 0.72,
                        "description": "Cyclical pattern with 3-month period",
                    },
                ],
                "correlations": [
                    {
                        "variables": "Variable A and B",
                        "coefficient": 0.78,
                        "significance": "high",
                    }
                ],
                "note": "This is simulated pattern identification. Implement with ML/statistical methods.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "pattern_identification",
                    "pattern_type": pattern_type,
                },
            )

            return json.dumps(patterns_result, indent=2)

        def generate_visualization(
            data_description: str, viz_type: str = "bar", title: str = ""
        ) -> str:
            """Generate data visualization specifications.

            Args:
                data_description: Description of the data to visualize.
                viz_type: Type of visualization (bar, line, scatter, heatmap, etc.).
                title: Optional title for the visualization.

            Returns:
                Visualization specification as JSON string.
            """
            viz_result = {
                "data": data_description,
                "visualization_type": viz_type,
                "title": title or f"{viz_type.title()} Chart",
                "configuration": {
                    "x_axis": "X-axis label",
                    "y_axis": "Y-axis label",
                    "color_scheme": "viridis",
                    "size": "800x600",
                },
                "insights_shown": [
                    f"Main trend visible in {viz_type} chart",
                    "Data distribution clearly illustrated",
                ],
                "note": "This is visualization specification. Implement with matplotlib/plotly in production.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "visualization",
                    "viz_type": viz_type,
                },
            )

            return json.dumps(viz_result, indent=2)

        def clean_data(
            data_description: str, cleaning_operations: str = ""
        ) -> str:
            """Clean and preprocess data.

            Args:
                data_description: Description of the data to clean.
                cleaning_operations: Comma-separated list of cleaning operations.

            Returns:
                Data cleaning results as JSON string.
            """
            operations = [
                op.strip() for op in cleaning_operations.split(",")
            ] if cleaning_operations else ["remove_duplicates", "handle_missing"]

            cleaning_result = {
                "data": data_description,
                "operations_performed": operations,
                "before": {
                    "records": 1000,
                    "missing_values": 45,
                    "duplicates": 12,
                },
                "after": {
                    "records": 988,
                    "missing_values": 0,
                    "duplicates": 0,
                },
                "changes_made": [
                    "Removed 12 duplicate records",
                    "Imputed 45 missing values using mean strategy",
                    "Standardized date formats",
                ],
                "data_quality_improvement": "15%",
                "note": "This is simulated data cleaning. Implement with pandas/numpy.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "data_cleaning",
                    "operations": operations,
                },
            )

            return json.dumps(cleaning_result, indent=2)

        def generate_report(
            analysis_summary: str, include_sections: str = ""
        ) -> str:
            """Generate a comprehensive data analysis report.

            Args:
                analysis_summary: Summary of the analysis performed.
                include_sections: Comma-separated sections to include.

            Returns:
                Report structure as JSON string.
            """
            sections = [
                s.strip() for s in include_sections.split(",")
            ] if include_sections else [
                "executive_summary",
                "methodology",
                "findings",
                "recommendations",
            ]

            report_result = {
                "title": "Data Analysis Report",
                "analysis_summary": analysis_summary,
                "sections": sections,
                "report_structure": {
                    section: f"Content for {section} section"
                    for section in sections
                },
                "key_findings": [
                    "Key finding 1 from comprehensive analysis",
                    "Key finding 2 with supporting data",
                    "Key finding 3 and implications",
                ],
                "recommendations": [
                    "Action item 1 based on data",
                    "Action item 2 for improvement",
                ],
                "note": "This is report structure. Generate actual content based on real analysis results.",
            }

            self.state_manager.add_result(
                self.name,
                {
                    "type": "report_generation",
                    "sections": sections,
                },
            )

            return json.dumps(report_result, indent=2)

        return [
            analyze_dataset,
            perform_statistical_analysis,
            identify_patterns,
            generate_visualization,
            clean_data,
            generate_report,
        ]

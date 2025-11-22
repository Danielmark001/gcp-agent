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

"""Multi-agent system for GCP Agent."""

from app.agents.base_agent import BaseSpecializedAgent
from app.agents.code_generation_agent import CodeGenerationAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.data_analysis_agent import DataAnalysisAgent
from app.agents.research_agent import ResearchAgent

__all__ = [
    "BaseSpecializedAgent",
    "CodeGenerationAgent",
    "CoordinatorAgent",
    "DataAnalysisAgent",
    "ResearchAgent",
]

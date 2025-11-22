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

"""Configuration management for the multi-agent system."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentConfig:
    """Configuration for agent behaviors and capabilities."""

    # Model configuration
    default_model: str = "gemini-2.0-flash"
    coordinator_model: str = "gemini-2.0-flash"
    research_model: str = "gemini-2.0-flash"
    code_gen_model: str = "gemini-2.0-flash"
    data_analysis_model: str = "gemini-2.0-flash"

    # Agent behavior configuration
    max_iterations: int = 10
    timeout_seconds: int = 300
    enable_parallel_execution: bool = True

    # Coordinator configuration
    coordinator_name: str = "coordinator"
    coordinator_enabled: bool = True

    # Research agent configuration
    research_name: str = "research_agent"
    research_max_search_results: int = 10
    research_enable_web_search: bool = True

    # Code generation agent configuration
    code_gen_name: str = "code_generation_agent"
    code_gen_enable_validation: bool = True
    code_gen_supported_languages: list[str] = field(
        default_factory=lambda: ["python", "javascript", "typescript", "go", "java"]
    )

    # Data analysis agent configuration
    data_analysis_name: str = "data_analysis_agent"
    data_analysis_max_dataset_size: int = 1000000  # 1MB
    data_analysis_supported_formats: list[str] = field(
        default_factory=lambda: ["csv", "json", "parquet", "excel"]
    )

    # Communication configuration
    enable_inter_agent_messages: bool = True
    message_queue_size: int = 100

    # Logging and monitoring
    enable_detailed_logging: bool = True
    log_level: str = "INFO"

    # GCP configuration
    project_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    )
    location: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "default_model": self.default_model,
            "coordinator_model": self.coordinator_model,
            "research_model": self.research_model,
            "code_gen_model": self.code_gen_model,
            "data_analysis_model": self.data_analysis_model,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "enable_parallel_execution": self.enable_parallel_execution,
            "coordinator_name": self.coordinator_name,
            "coordinator_enabled": self.coordinator_enabled,
            "research_name": self.research_name,
            "research_max_search_results": self.research_max_search_results,
            "research_enable_web_search": self.research_enable_web_search,
            "code_gen_name": self.code_gen_name,
            "code_gen_enable_validation": self.code_gen_enable_validation,
            "code_gen_supported_languages": self.code_gen_supported_languages,
            "data_analysis_name": self.data_analysis_name,
            "data_analysis_max_dataset_size": self.data_analysis_max_dataset_size,
            "data_analysis_supported_formats": self.data_analysis_supported_formats,
            "enable_inter_agent_messages": self.enable_inter_agent_messages,
            "message_queue_size": self.message_queue_size,
            "enable_detailed_logging": self.enable_detailed_logging,
            "log_level": self.log_level,
            "project_id": self.project_id,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "AgentConfig":
        """Create configuration from dictionary.

        Args:
            config_dict: Dictionary with configuration values.

        Returns:
            AgentConfig instance.
        """
        return cls(**config_dict)

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables.

        Returns:
            AgentConfig instance with values from environment.
        """
        return cls(
            default_model=os.environ.get("AGENT_DEFAULT_MODEL", "gemini-2.0-flash"),
            max_iterations=int(os.environ.get("AGENT_MAX_ITERATIONS", "10")),
            timeout_seconds=int(os.environ.get("AGENT_TIMEOUT_SECONDS", "300")),
            enable_parallel_execution=os.environ.get(
                "AGENT_ENABLE_PARALLEL", "true"
            ).lower()
            == "true",
            research_enable_web_search=os.environ.get(
                "RESEARCH_ENABLE_WEB_SEARCH", "true"
            ).lower()
            == "true",
            code_gen_enable_validation=os.environ.get(
                "CODE_GEN_ENABLE_VALIDATION", "true"
            ).lower()
            == "true",
            enable_detailed_logging=os.environ.get(
                "AGENT_ENABLE_DETAILED_LOGGING", "true"
            ).lower()
            == "true",
            log_level=os.environ.get("AGENT_LOG_LEVEL", "INFO"),
        )


# Global configuration instance
_global_config: AgentConfig | None = None


def get_agent_config() -> AgentConfig:
    """Get the global agent configuration.

    Returns:
        The global AgentConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = AgentConfig()
    return _global_config


def set_agent_config(config: AgentConfig) -> None:
    """Set the global agent configuration.

    Args:
        config: The AgentConfig to set as global.
    """
    global _global_config
    _global_config = config

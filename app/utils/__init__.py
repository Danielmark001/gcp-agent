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
Utilities package for multi-agent architecture.

This package provides comprehensive utilities for:
- Error handling and recovery
- Input/output validation
- Monitoring and observability
- Debugging and profiling
"""

# Error Handling
from app.utils.error_handling import (
    AgentError,
    AgentErrorCategory,
    AgentErrorSeverity,
    CommunicationError,
    ConfigurationError,
    ErrorContext,
    ErrorRecord,
    ErrorRecoveryHandler,
    ModelInferenceError,
    RateLimitError,
    RecoveryStrategy,
    ResourceError,
    RetryConfig,
    TimeoutError,
    ToolExecutionError,
    ValidationError,
    calculate_backoff_delay,
    retry_with_backoff,
    safe_execute,
    with_fallback,
)

# Validation
from app.utils.validation import (
    InputValidator,
    OutputConstraints,
    OutputValidator,
    RateLimitConfig,
    RateLimiter,
    SlidingWindowRateLimiter,
    ToolInputConstraints,
    async_timeout,
    rate_limit,
    timeout,
    validate_tool_input,
    validate_tool_output,
    validated_tool,
)

# Monitoring
from app.utils.monitoring import (
    ComponentHealth,
    ErrorAggregator,
    ErrorMetrics,
    HealthCheckResult,
    HealthChecker,
    HealthStatus,
    LogContext,
    LogLevel,
    MetricsCollector,
    PerformanceMetrics,
    StructuredLogger,
    TraceContext,
    TraceManager,
    monitor_performance,
    traced_operation,
)

# Debugging
from app.utils.debug import (
    AgentStateInspector,
    AgentStateSnapshot,
    CommunicationLog,
    CommunicationLogger,
    DebugConfig,
    DebugLevel,
    DebugManager,
    MessageType,
    PerformanceProfiler,
    ProfileResult,
    debug_inspect,
    debug_trace,
    disable_debug_mode,
    dump_debug_info,
    enable_debug_mode,
    print_agent_state,
    profile_function,
)

__all__ = [
    # Error Handling
    "AgentError",
    "AgentErrorCategory",
    "AgentErrorSeverity",
    "CommunicationError",
    "ConfigurationError",
    "ErrorContext",
    "ErrorRecord",
    "ErrorRecoveryHandler",
    "ModelInferenceError",
    "RateLimitError",
    "RecoveryStrategy",
    "ResourceError",
    "RetryConfig",
    "TimeoutError",
    "ToolExecutionError",
    "ValidationError",
    "calculate_backoff_delay",
    "retry_with_backoff",
    "safe_execute",
    "with_fallback",
    # Validation
    "InputValidator",
    "OutputConstraints",
    "OutputValidator",
    "RateLimitConfig",
    "RateLimiter",
    "SlidingWindowRateLimiter",
    "ToolInputConstraints",
    "async_timeout",
    "rate_limit",
    "timeout",
    "validate_tool_input",
    "validate_tool_output",
    "validated_tool",
    # Monitoring
    "ComponentHealth",
    "ErrorAggregator",
    "ErrorMetrics",
    "HealthCheckResult",
    "HealthChecker",
    "HealthStatus",
    "LogContext",
    "LogLevel",
    "MetricsCollector",
    "PerformanceMetrics",
    "StructuredLogger",
    "TraceContext",
    "TraceManager",
    "monitor_performance",
    "traced_operation",
    # Debugging
    "AgentStateInspector",
    "AgentStateSnapshot",
    "CommunicationLog",
    "CommunicationLogger",
    "DebugConfig",
    "DebugLevel",
    "DebugManager",
    "MessageType",
    "PerformanceProfiler",
    "ProfileResult",
    "debug_inspect",
    "debug_trace",
    "disable_debug_mode",
    "dump_debug_info",
    "enable_debug_mode",
    "print_agent_state",
    "profile_function",
]

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
Example Usage of Error Handling and Debugging Utilities

This module demonstrates how to use the various utilities in real-world scenarios.
"""

import random
import time
from typing import Any

# Error Handling
from app.utils.error_handling import (
    AgentErrorSeverity,
    ErrorContext,
    ErrorRecoveryHandler,
    RecoveryStrategy,
    RetryConfig,
    ToolExecutionError,
    retry_with_backoff,
    safe_execute,
    with_fallback,
)

# Validation
from app.utils.validation import (
    OutputConstraints,
    RateLimitConfig,
    ToolInputConstraints,
    validated_tool,
)

# Monitoring
from app.utils.monitoring import (
    HealthChecker,
    HealthStatus,
    LogContext,
    MetricsCollector,
    StructuredLogger,
    TraceManager,
    monitor_performance,
)

# Debugging
from app.utils.debug import (
    AgentStateInspector,
    CommunicationLogger,
    DebugLevel,
    MessageType,
    debug_trace,
    enable_debug_mode,
)


# ============================================================================
# Example 1: Weather Agent with Full Error Handling
# ============================================================================


class WeatherAgent:
    """Example weather agent with comprehensive error handling and monitoring."""

    def __init__(self, name: str = "weather_agent"):
        """Initialize weather agent with monitoring."""
        self.name = name
        self.logger = StructuredLogger(name)
        self.trace_manager = TraceManager()
        self.recovery_handler = ErrorRecoveryHandler(
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60.0,
        )
        self.state_inspector = AgentStateInspector()
        self.metrics_collector = MetricsCollector()
        self.cache = {}

    @debug_trace
    @monitor_performance("get_weather")
    @validated_tool(
        input_constraints=ToolInputConstraints(
            max_string_length=100,
            required_fields=["location"],
        ),
        output_constraints=OutputConstraints(max_output_size=10000),
        rate_limit_config=RateLimitConfig(requests_per_second=10),
        timeout_seconds=30,
    )
    @retry_with_backoff(RetryConfig(max_attempts=3))
    def get_weather(self, location: str) -> dict[str, Any]:
        """Get weather data with full error handling.

        Args:
            location: Location to get weather for

        Returns:
            Weather data dictionary
        """
        # Create log context
        context = LogContext(
            agent_name=self.name,
            operation="get_weather",
            metadata={"location": location},
        )

        # Start trace
        trace_ctx = self.trace_manager.start_trace(
            operation_name="get_weather",
            agent_name=self.name,
            attributes={"location": location},
        )

        try:
            self.logger.info(f"Fetching weather for {location}", context=context)

            # Capture state snapshot
            self.state_inspector.capture_snapshot(
                agent_name=self.name,
                state_vars={"cache_size": len(self.cache)},
                active_ops=["get_weather"],
            )

            # Check cache
            if location in self.cache:
                self.logger.info("Returning cached result", context=context)
                return self.cache[location]

            # Simulate API call (with random failures for demonstration)
            weather_data = self._fetch_weather_api(location)

            # Cache result
            self.cache[location] = weather_data

            # End trace successfully
            self.trace_manager.end_trace(trace_ctx.span_id, status="success")
            self.logger.info("Weather data retrieved successfully", context=context)

            return weather_data

        except Exception as e:
            # Create error
            error = ToolExecutionError(
                message=f"Failed to get weather for {location}",
                tool_name="get_weather",
                tool_args={"location": location},
                severity=AgentErrorSeverity.MEDIUM,
                agent_name=self.name,
                original_exception=e,
            )

            # Create error context
            error_context = ErrorContext(
                error_id=trace_ctx.trace_id,
                agent_name=self.name,
                operation="get_weather",
                metadata={"location": location},
            )

            # Handle error
            self.recovery_handler.handle_error(
                error=error,
                context=error_context,
                strategy=RecoveryStrategy.CIRCUIT_BREAKER,
            )

            # End trace with error
            self.trace_manager.end_trace(trace_ctx.span_id, status="error", error=e)
            self.logger.error(f"Error getting weather: {e}", context=context)

            raise

    def _fetch_weather_api(self, location: str) -> dict[str, Any]:
        """Simulate fetching from weather API."""
        # Simulate network delay
        time.sleep(0.1)

        # Simulate random failures
        if random.random() < 0.2:  # 20% failure rate
            raise Exception("API temporarily unavailable")

        # Return mock data
        if "san francisco" in location.lower() or "sf" in location.lower():
            return {
                "location": location,
                "temperature": 60,
                "condition": "foggy",
                "humidity": 80,
                "wind_speed": 10,
            }
        else:
            return {
                "location": location,
                "temperature": 75,
                "condition": "sunny",
                "humidity": 50,
                "wind_speed": 5,
            }

    def get_weather_with_fallback(self, location: str) -> dict[str, Any]:
        """Get weather with fallback to cached or default data."""

        def fallback() -> dict[str, Any]:
            # Try cache first
            if location in self.cache:
                self.logger.warning(f"Using cached data for {location}")
                return self.cache[location]

            # Return default data
            self.logger.warning(f"Using default data for {location}")
            return {
                "location": location,
                "temperature": 70,
                "condition": "unknown",
                "humidity": 60,
                "wind_speed": 5,
                "source": "default",
            }

        return with_fallback(
            lambda: self.get_weather(location),
            fallback,
        )()


# ============================================================================
# Example 2: Multi-Agent Coordinator with Communication Logging
# ============================================================================


class MultiAgentCoordinator:
    """Coordinator that manages multiple agents with full monitoring."""

    def __init__(self, name: str = "coordinator"):
        """Initialize coordinator."""
        self.name = name
        self.logger = StructuredLogger(name)
        self.comm_logger = CommunicationLogger(max_logs=10000)
        self.health_checker = HealthChecker()
        self.agents = {}

    def register_agent(self, agent_name: str, agent: Any) -> None:
        """Register an agent with the coordinator."""
        self.agents[agent_name] = agent
        self.logger.info(f"Registered agent: {agent_name}")

        # Register health check
        def health_check():
            from app.utils.monitoring import ComponentHealth

            try:
                # Check if agent is responsive
                hasattr(agent, "get_weather")  # Basic check
                return ComponentHealth(
                    name=agent_name,
                    status=HealthStatus.HEALTHY,
                    message=f"Agent {agent_name} is operational",
                )
            except Exception as e:
                return ComponentHealth(
                    name=agent_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Agent {agent_name} health check failed: {e}",
                )

        self.health_checker.register_check(agent_name, health_check)

    @debug_trace
    def delegate_task(
        self, agent_name: str, task: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Delegate a task to a specific agent.

        Args:
            agent_name: Name of the agent
            task: Task to perform
            **kwargs: Task arguments

        Returns:
            Task result
        """
        # Log communication
        log_entry = self.comm_logger.log_message(
            message_type=MessageType.REQUEST,
            source_agent=self.name,
            target_agent=agent_name,
            operation=task,
            payload=kwargs,
        )

        start_time = time.time()

        try:
            agent = self.agents.get(agent_name)
            if not agent:
                raise ValueError(f"Agent not found: {agent_name}")

            # Execute task
            result = getattr(agent, task)(**kwargs)

            # Update communication log
            duration_ms = (time.time() - start_time) * 1000
            self.comm_logger.update_response(
                log_id=log_entry.log_id,
                response={"result": result},
                duration_ms=duration_ms,
                success=True,
            )

            return result

        except Exception as e:
            # Update communication log with error
            duration_ms = (time.time() - start_time) * 1000
            self.comm_logger.update_response(
                log_id=log_entry.log_id,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e),
            )

            self.logger.error(f"Task delegation failed: {e}")
            raise

    def get_communication_stats(self) -> dict[str, Any]:
        """Get communication statistics."""
        return self.comm_logger.analyze_communication_patterns()

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of all agents."""
        result = self.health_checker.run_all_checks()
        return {
            "overall_status": result.overall_status.value,
            "uptime_seconds": result.uptime_seconds,
            "components": [
                {
                    "name": comp.name,
                    "status": comp.status.value,
                    "message": comp.message,
                }
                for comp in result.components
            ],
        }


# ============================================================================
# Example 3: Demonstrating Safe Execution
# ============================================================================


def process_user_query_safely(
    query: str, agent: WeatherAgent
) -> tuple[dict[str, Any] | None, Exception | None]:
    """Process user query with safe execution wrapper.

    Args:
        query: User query
        agent: Weather agent

    Returns:
        Tuple of (result, error)
    """
    # Create recovery handler
    recovery_handler = ErrorRecoveryHandler()

    # Create error context
    error_context = ErrorContext(
        agent_name=agent.name,
        operation="process_query",
        metadata={"query": query},
    )

    # Extract location from query (simplified)
    location = query.replace("weather in ", "").replace("?", "").strip()

    # Safe execution
    result, error = safe_execute(
        func=agent.get_weather,
        location=location,
        default={"location": location, "error": "Failed to fetch weather"},
        error_handler=recovery_handler,
        context=error_context,
    )

    return result, error


# ============================================================================
# Main Example
# ============================================================================


def main():
    """Run example demonstrations."""

    # Enable debug mode
    enable_debug_mode(
        level=DebugLevel.DEBUG,
        log_function_calls=True,
        profile_performance=True,
    )

    print("\n" + "=" * 60)
    print("Error Handling & Debugging System Examples")
    print("=" * 60 + "\n")

    # Example 1: Single Weather Agent
    print("\n--- Example 1: Weather Agent ---\n")

    weather_agent = WeatherAgent()

    # Test successful request
    try:
        result = weather_agent.get_weather("San Francisco")
        print(f"✓ Weather data: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test with fallback
    print("\n--- Testing with fallback ---\n")
    result = weather_agent.get_weather_with_fallback("San Francisco")
    print(f"✓ Weather (with fallback): {result}")

    # Get metrics
    metrics = weather_agent.metrics_collector.get_metrics("get_weather")
    if metrics and "get_weather" in metrics:
        m = metrics["get_weather"]
        print(f"\nPerformance Metrics:")
        print(f"  Total calls: {m.call_count}")
        print(f"  Avg duration: {m.avg_duration_ms:.2f}ms")
        print(f"  Errors: {m.error_count}")

    # Example 2: Multi-Agent Coordinator
    print("\n--- Example 2: Multi-Agent Coordinator ---\n")

    coordinator = MultiAgentCoordinator()
    coordinator.register_agent("weather_agent", weather_agent)

    # Delegate task
    try:
        result = coordinator.delegate_task(
            "weather_agent", "get_weather", location="New York"
        )
        print(f"✓ Delegated task result: {result}")
    except Exception as e:
        print(f"✗ Delegation error: {e}")

    # Get communication stats
    comm_stats = coordinator.get_communication_stats()
    print(f"\nCommunication Stats:")
    print(f"  Total messages: {comm_stats.get('total_messages', 0)}")
    print(f"  Success rate: {comm_stats.get('success_rate', 0):.2%}")

    # Get health status
    health = coordinator.get_health_status()
    print(f"\nHealth Status:")
    print(f"  Overall: {health['overall_status']}")
    print(f"  Uptime: {health['uptime_seconds']:.2f}s")
    for comp in health["components"]:
        print(f"  - {comp['name']}: {comp['status']}")

    # Example 3: Safe Execution
    print("\n--- Example 3: Safe Execution ---\n")

    result, error = process_user_query_safely(
        "weather in San Francisco?", weather_agent
    )

    if error:
        print(f"✗ Query failed: {error}")
    else:
        print(f"✓ Query result: {result}")

    # Get state snapshots
    print("\n--- Agent State Snapshots ---\n")
    snapshots = weather_agent.state_inspector.get_snapshots(
        weather_agent.name, limit=5
    )
    print(f"Captured {len(snapshots)} state snapshots")
    if snapshots:
        latest = snapshots[-1]
        print(f"Latest snapshot:")
        print(f"  Timestamp: {latest.timestamp}")
        print(f"  Memory: {latest.memory_usage_mb:.2f} MB")
        print(f"  Threads: {latest.thread_count}")
        print(f"  State: {latest.state_variables}")

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

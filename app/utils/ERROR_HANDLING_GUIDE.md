# Error Handling & Debugging Guide

This guide provides comprehensive documentation for the error handling and debugging utilities in the multi-agent architecture.

## Overview

The error handling and debugging system consists of four main modules:

1. **error_handling.py** - Custom exceptions, retry logic, and recovery strategies
2. **validation.py** - Input/output validation, rate limiting, and timeout handling
3. **monitoring.py** - Logging, tracing, metrics, and health checks
4. **debug.py** - State inspection, communication logging, and profiling

## Table of Contents

- [Error Handling](#error-handling)
  - [Custom Exceptions](#custom-exceptions)
  - [Retry Logic](#retry-logic)
  - [Error Recovery](#error-recovery)
  - [Fallback Mechanisms](#fallback-mechanisms)
- [Validation](#validation)
  - [Input Validation](#input-validation)
  - [Output Validation](#output-validation)
  - [Rate Limiting](#rate-limiting)
  - [Timeout Handling](#timeout-handling)
- [Monitoring](#monitoring)
  - [Structured Logging](#structured-logging)
  - [Distributed Tracing](#distributed-tracing)
  - [Error Aggregation](#error-aggregation)
  - [Health Checks](#health-checks)
  - [Performance Metrics](#performance-metrics)
- [Debugging](#debugging)
  - [Debug Configuration](#debug-configuration)
  - [State Inspection](#state-inspection)
  - [Communication Logging](#communication-logging)
  - [Performance Profiling](#performance-profiling)

---

## Error Handling

### Custom Exceptions

The system provides specialized exception classes for different error types:

```python
from app.utils.error_handling import (
    AgentError,
    ToolExecutionError,
    ModelInferenceError,
    ValidationError,
    TimeoutError,
    RateLimitError,
    ResourceError,
    CommunicationError,
    ConfigurationError,
)

# Example: Raise a tool execution error
try:
    result = execute_tool(tool_name, args)
except Exception as e:
    raise ToolExecutionError(
        message="Failed to execute weather tool",
        tool_name="get_weather",
        tool_args={"location": "SF"},
        severity=AgentErrorSeverity.HIGH,
        agent_name="weather_agent",
        original_exception=e,
    )
```

**Error Properties:**
- `message` - Human-readable error message
- `category` - Error category (TOOL_EXECUTION, MODEL_INFERENCE, etc.)
- `severity` - Severity level (LOW, MEDIUM, HIGH, CRITICAL)
- `agent_name` - Name of the agent where error occurred
- `recoverable` - Whether the error can be recovered from
- `original_exception` - The underlying exception if wrapping another error
- `context` - Additional context information

### Retry Logic

Implement automatic retries with exponential backoff:

```python
from app.utils.error_handling import retry_with_backoff, RetryConfig

# Using decorator
@retry_with_backoff(RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
))
def call_external_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# Custom retry callback
def on_retry_callback(attempt, exception):
    logger.warning(f"Retry attempt {attempt}: {exception}")

@retry_with_backoff(
    RetryConfig(max_attempts=3),
    on_retry=on_retry_callback,
)
def unstable_operation():
    # Operation that might fail
    pass
```

**RetryConfig Parameters:**
- `max_attempts` - Maximum number of retry attempts (default: 3)
- `initial_delay` - Initial delay in seconds (default: 1.0)
- `max_delay` - Maximum delay in seconds (default: 60.0)
- `exponential_base` - Base for exponential backoff (default: 2.0)
- `jitter` - Add randomness to delay (default: True)

### Error Recovery

Handle errors with sophisticated recovery strategies:

```python
from app.utils.error_handling import (
    ErrorRecoveryHandler,
    ErrorContext,
    RecoveryStrategy,
)

# Initialize recovery handler
recovery_handler = ErrorRecoveryHandler(
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=60.0,
)

# Handle an error
error = ToolExecutionError("Tool failed", tool_name="my_tool")
context = ErrorContext(
    error_id="err_123",
    agent_name="my_agent",
    operation="process_query",
)

error_record = recovery_handler.handle_error(
    error=error,
    context=context,
    strategy=RecoveryStrategy.CIRCUIT_BREAKER,
)

# Attempt recovery
result = recovery_handler.recover(
    func=lambda: execute_tool(),
    error=error,
    context=context,
    fallback_func=lambda: use_cached_result(),
)
```

**Recovery Strategies:**
- `RETRY` - Retry the operation with exponential backoff
- `FALLBACK` - Use a fallback function/agent
- `SKIP` - Skip the failed operation and continue
- `ESCALATE` - Escalate to a higher-level handler
- `CIRCUIT_BREAKER` - Open circuit after threshold failures

### Fallback Mechanisms

Implement fallback behavior for critical operations:

```python
from app.utils.error_handling import with_fallback, safe_execute

# Simple fallback decorator
@with_fallback(
    primary_func=lambda x: primary_agent.process(x),
    fallback_func=lambda x: fallback_agent.process(x),
    exceptions=(ModelInferenceError, TimeoutError),
)
def process_with_fallback(query):
    pass

# Safe execution wrapper
result, error = safe_execute(
    func=risky_operation,
    arg1="value",
    default="default_result",
    error_handler=recovery_handler,
    context=error_context,
)

if error:
    logger.error(f"Operation failed: {error}")
    # Handle error appropriately
```

---

## Validation

### Input Validation

Validate inputs to agent tools:

```python
from app.utils.validation import (
    validate_tool_input,
    ToolInputConstraints,
    InputValidator,
)

# Using decorator
@validate_tool_input(ToolInputConstraints(
    max_string_length=5000,
    max_list_size=100,
    forbidden_patterns=[r'<script>', r'DROP\s+TABLE'],
    required_fields=['query', 'user_id'],
))
def search_tool(query: str, user_id: str, filters: list = None) -> dict:
    # Tool implementation
    return {"results": [...]}

# Manual validation
validator = InputValidator(ToolInputConstraints(
    max_string_length=1000,
    allowed_types=['str', 'int', 'list', 'dict'],
))

try:
    validator.validate_input(user_input, field_name="user_query")
except ValidationError as e:
    logger.error(f"Validation failed: {e.message}")
```

**Constraint Parameters:**
- `max_string_length` - Maximum length for strings
- `max_list_size` - Maximum size for lists
- `max_dict_size` - Maximum size for dictionaries
- `max_nesting_depth` - Maximum nesting depth for data structures
- `allowed_types` - List of allowed type names
- `forbidden_patterns` - Regex patterns to reject
- `required_fields` - Required dictionary fields

### Output Validation

Validate outputs from agent operations:

```python
from app.utils.validation import validate_tool_output, OutputConstraints

@validate_tool_output(OutputConstraints(
    max_output_size=50000,
    required_fields=['status', 'data'],
    allow_none=False,
))
def process_data(input_data: dict) -> dict:
    # Processing logic
    return {
        'status': 'success',
        'data': processed_results,
        'metadata': {...}
    }
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from app.utils.validation import rate_limit, RateLimitConfig, RateLimiter

# Using decorator
@rate_limit(RateLimitConfig(
    requests_per_second=10,
    burst_size=20,
    wait_on_limit=True,
))
def api_call(endpoint: str) -> dict:
    return make_request(endpoint)

# Manual rate limiting
limiter = RateLimiter(RateLimitConfig(
    requests_per_minute=100,
    wait_on_limit=False,  # Raise error instead of waiting
))

try:
    limiter.acquire()
    result = expensive_operation()
except RateLimitError as e:
    logger.warning(f"Rate limit exceeded, retry after {e.retry_after}s")
```

### Timeout Handling

Add timeouts to prevent hanging operations:

```python
from app.utils.validation import timeout, async_timeout

# Synchronous timeout
@timeout(seconds=30, error_message="Search timed out")
def search_database(query: str) -> list:
    # Long-running database query
    return results

# Asynchronous timeout
@async_timeout(seconds=10)
async def fetch_remote_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Combined Validation

Use all validation features together:

```python
from app.utils.validation import validated_tool

@validated_tool(
    input_constraints=ToolInputConstraints(max_string_length=1000),
    output_constraints=OutputConstraints(max_output_size=10000),
    rate_limit_config=RateLimitConfig(requests_per_second=5),
    timeout_seconds=30,
)
def complex_tool(query: str) -> dict:
    # Tool implementation with all validations applied
    return process_query(query)
```

---

## Monitoring

### Structured Logging

Enhanced logging with context:

```python
from app.utils.monitoring import StructuredLogger, LogContext, LogLevel

# Initialize logger
logger = StructuredLogger(
    name="my_agent",
    use_cloud_logging=True,
    project_id="my-gcp-project",
)

# Log with context
context = LogContext(
    agent_name="weather_agent",
    operation="get_forecast",
    request_id="req_123",
    session_id="session_456",
    metadata={"location": "San Francisco"},
)

logger.info("Processing weather request", context=context)
logger.error("Failed to fetch data", context=context, error_code=500)
```

### Distributed Tracing

Track operations across agents:

```python
from app.utils.monitoring import TraceManager, traced_operation

# Initialize trace manager
trace_manager = TraceManager(project_id="my-gcp-project")

# Using decorator
@traced_operation("process_user_query", trace_manager=trace_manager)
def process_query(query: str) -> str:
    # Operation is automatically traced
    return result

# Manual tracing
trace_ctx = trace_manager.start_trace(
    operation_name="multi_agent_workflow",
    agent_name="coordinator",
)

# Add events
trace_manager.add_event(
    span_id=trace_ctx.span_id,
    event_name="agent_called",
    attributes={"agent": "weather_agent"},
)

# End trace
trace_manager.end_trace(
    span_id=trace_ctx.span_id,
    status="success",
)
```

### Error Aggregation

Track and analyze errors:

```python
from app.utils.monitoring import ErrorAggregator

# Initialize aggregator
aggregator = ErrorAggregator(
    max_recent_errors=200,
    error_rate_window=60,
)

# Record errors
aggregator.record_error(error_record)

# Get metrics
metrics = aggregator.get_metrics()
print(f"Total errors: {metrics.total_errors}")
print(f"Error rate: {metrics.error_rate_per_minute}/min")
print(f"Errors by category: {metrics.errors_by_category}")

# Get filtered errors
tool_errors = aggregator.get_errors_by_category("tool_execution")
agent_errors = aggregator.get_errors_by_agent("weather_agent")
```

### Health Checks

Monitor agent health:

```python
from app.utils.monitoring import HealthChecker, ComponentHealth, HealthStatus

# Initialize health checker
health_checker = HealthChecker()

# Register health check functions
def check_database_health() -> ComponentHealth:
    try:
        # Check database connection
        db.ping()
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection OK",
        )
    except Exception as e:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {e}",
        )

health_checker.register_check("database", check_database_health)

# Run health checks
result = health_checker.run_all_checks()
print(f"Overall status: {result.overall_status}")
print(f"Uptime: {result.uptime_seconds}s")

for component in result.components:
    print(f"{component.name}: {component.status}")
```

### Performance Metrics

Collect performance metrics:

```python
from app.utils.monitoring import monitor_performance, MetricsCollector

# Initialize collector
collector = MetricsCollector(max_samples=1000)

# Using decorator
@monitor_performance("query_processing", collector=collector)
def process_query(query: str) -> str:
    # Function is automatically monitored
    return result

# Get metrics
metrics = collector.get_metrics("query_processing")
if metrics:
    print(f"Calls: {metrics['query_processing'].call_count}")
    print(f"Avg duration: {metrics['query_processing'].avg_duration_ms}ms")
    print(f"P95 duration: {metrics['query_processing'].p95_duration_ms}ms")
```

---

## Debugging

### Debug Configuration

Enable and configure debug mode:

```python
from app.utils.debug import enable_debug_mode, DebugLevel, DebugManager

# Enable debug mode
enable_debug_mode(
    level=DebugLevel.DEBUG,
    log_function_calls=True,
    log_function_args=True,
    log_function_results=True,
    profile_performance=True,
    save_debug_logs=True,
)

# Or use environment variables
# AGENT_DEBUG=true
# AGENT_DEBUG_LEVEL=debug
# AGENT_DEBUG_PROFILE=true
# AGENT_DEBUG_TRACE=true

# Check if debug is enabled
debug_manager = DebugManager()
if debug_manager.is_enabled():
    print("Debug mode is active")
```

### State Inspection

Inspect agent state:

```python
from app.utils.debug import AgentStateInspector, print_agent_state

# Initialize inspector
inspector = AgentStateInspector()

# Capture snapshots
snapshot = inspector.capture_snapshot(
    agent_name="weather_agent",
    state_vars={
        "cache_size": 100,
        "last_update": datetime.now(),
        "active_requests": 5,
    },
    active_ops=["get_weather", "get_forecast"],
)

# Get snapshots
recent_snapshots = inspector.get_snapshots("weather_agent", limit=10)
latest = inspector.get_latest_snapshot("weather_agent")

# Compare snapshots
comparison = inspector.compare_snapshots(snapshot1, snapshot2)
print(f"Memory change: {comparison['memory_diff_mb']} MB")
print(f"State changes: {comparison['state_changes']}")

# Print agent state
print_agent_state(agent, verbose=True)
```

### Communication Logging

Log and analyze inter-agent communication:

```python
from app.utils.debug import CommunicationLogger, MessageType

# Initialize logger
comm_logger = CommunicationLogger(max_logs=10000)

# Log messages
log_entry = comm_logger.log_message(
    message_type=MessageType.REQUEST,
    source_agent="coordinator",
    target_agent="weather_agent",
    operation="get_weather",
    payload={"location": "SF"},
)

# Update with response
comm_logger.update_response(
    log_id=log_entry.log_id,
    response={"temperature": 60, "condition": "foggy"},
    duration_ms=150.5,
    success=True,
)

# Analyze patterns
analysis = comm_logger.analyze_communication_patterns()
print(f"Total messages: {analysis['total_messages']}")
print(f"Success rate: {analysis['success_rate']}")
print(f"Most active pairs: {analysis['most_active_agent_pairs']}")

# Export logs
comm_logger.export_logs("/tmp/communication_logs.json")
```

### Performance Profiling

Profile function performance:

```python
from app.utils.debug import profile_function, PerformanceProfiler

# Using decorator
@profile_function("data_processing")
def process_large_dataset(data: list) -> dict:
    # Complex processing
    return results

# Manual profiling
profiler = PerformanceProfiler()

profiler.start_profiling("my_operation")
# ... code to profile ...
result = profiler.stop_profiling("my_operation")

print(f"Total time: {result.total_time}s")
print(f"Num calls: {result.num_calls}")
print(f"Top functions:")
for func_info in result.top_functions[:5]:
    print(f"  {func_info['function']}: {func_info['cumulative_time']}s")
```

### Debug Decorators

Use debug decorators for automatic tracing:

```python
from app.utils.debug import debug_trace, debug_inspect

@debug_trace
def complex_operation(x: int, y: int) -> int:
    # Function execution is traced when debug mode is enabled
    return x + y

@debug_inspect
def data_transformer(data: dict) -> dict:
    # Arguments and return values are logged in trace mode
    return transformed_data
```

---

## Complete Example

Here's a complete example using all components together:

```python
from app.utils.error_handling import (
    retry_with_backoff,
    RetryConfig,
    ErrorRecoveryHandler,
    ErrorContext,
)
from app.utils.validation import validated_tool, ToolInputConstraints, OutputConstraints, RateLimitConfig
from app.utils.monitoring import (
    StructuredLogger,
    LogContext,
    TraceManager,
    ErrorAggregator,
    monitor_performance,
)
from app.utils.debug import debug_trace, enable_debug_mode, DebugLevel

# Enable debug mode
enable_debug_mode(level=DebugLevel.DEBUG)

# Initialize components
logger = StructuredLogger("weather_agent")
trace_manager = TraceManager()
error_aggregator = ErrorAggregator()
recovery_handler = ErrorRecoveryHandler()

@debug_trace
@monitor_performance("get_weather_data")
@validated_tool(
    input_constraints=ToolInputConstraints(max_string_length=100),
    output_constraints=OutputConstraints(max_output_size=10000),
    rate_limit_config=RateLimitConfig(requests_per_second=10),
    timeout_seconds=30,
)
@retry_with_backoff(RetryConfig(max_attempts=3))
def get_weather(location: str) -> dict:
    """Get weather data with full error handling and monitoring."""

    context = LogContext(
        agent_name="weather_agent",
        operation="get_weather",
        metadata={"location": location},
    )

    # Start trace
    trace_ctx = trace_manager.start_trace(
        operation_name="get_weather",
        agent_name="weather_agent",
    )

    try:
        logger.info(f"Fetching weather for {location}", context=context)

        # Simulate API call
        weather_data = fetch_from_api(location)

        trace_manager.end_trace(trace_ctx.span_id, status="success")
        logger.info("Weather data retrieved successfully", context=context)

        return weather_data

    except Exception as e:
        error = ToolExecutionError(
            message=f"Failed to get weather for {location}",
            tool_name="get_weather",
            tool_args={"location": location},
            original_exception=e,
        )

        error_context = ErrorContext(
            error_id=trace_ctx.trace_id,
            agent_name="weather_agent",
            operation="get_weather",
        )

        error_record = recovery_handler.handle_error(error, error_context)
        error_aggregator.record_error(error_record)

        trace_manager.end_trace(trace_ctx.span_id, status="error", error=e)
        logger.error(f"Error getting weather: {e}", context=context)

        raise

# Usage
try:
    weather = get_weather("San Francisco")
    print(f"Weather: {weather}")
except Exception as e:
    print(f"Failed to get weather: {e}")
```

---

## Best Practices

1. **Error Handling**
   - Always use appropriate exception types
   - Include context information in errors
   - Set appropriate severity levels
   - Use circuit breakers for external services

2. **Validation**
   - Validate all external inputs
   - Set reasonable limits on data sizes
   - Use rate limiting for expensive operations
   - Add timeouts to prevent hanging

3. **Monitoring**
   - Use structured logging with context
   - Implement distributed tracing for multi-agent workflows
   - Monitor error rates and patterns
   - Set up health checks for critical components

4. **Debugging**
   - Enable debug mode during development
   - Use profiling to identify bottlenecks
   - Track communication between agents
   - Capture state snapshots for analysis

5. **Production**
   - Disable verbose debug logging in production
   - Keep error aggregation for analysis
   - Monitor health check endpoints
   - Set up alerts for high error rates

---

## Environment Variables

Configure the system using environment variables:

```bash
# Debug Configuration
export AGENT_DEBUG=true
export AGENT_DEBUG_LEVEL=debug
export AGENT_DEBUG_PROFILE=true
export AGENT_DEBUG_TRACE=true

# Google Cloud
export GOOGLE_CLOUD_PROJECT=my-project
export GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Troubleshooting

### High Error Rates

1. Check error aggregator metrics
2. Filter errors by category and agent
3. Look for patterns in error messages
4. Verify circuit breakers aren't stuck open

### Performance Issues

1. Enable performance profiling
2. Check P95 and P99 latencies
3. Look for slow operations in traces
4. Analyze communication patterns

### Memory Leaks

1. Capture periodic state snapshots
2. Compare memory usage over time
3. Check for unbounded collections
4. Review error history size limits

### Communication Failures

1. Enable communication logging
2. Analyze message success rates
3. Check for timeout patterns
4. Verify agent health checks

---

## Contributing

When adding new error types or monitoring capabilities:

1. Follow existing patterns and naming conventions
2. Add comprehensive docstrings
3. Include usage examples
4. Update this documentation
5. Add tests for new functionality

---

## License

Copyright 2025 Google LLC. Licensed under the Apache License, Version 2.0.

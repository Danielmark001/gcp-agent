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
Monitoring and Observability for Multi-Agent Architecture

This module provides comprehensive monitoring capabilities including:
- Enhanced logging for agent operations
- Trace correlation for multi-agent workflows
- Error reporting and aggregation
- Health check endpoints for agents
"""

import functools
import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from pydantic import BaseModel, Field

from app.utils.error_handling import ErrorRecord

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Structured Logging
# ============================================================================


class LogLevel(str, Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogContext(BaseModel):
    """Context information for structured logging."""

    agent_name: str | None = None
    operation: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuredLogger:
    """Enhanced structured logger for agent operations."""

    def __init__(
        self,
        name: str,
        use_cloud_logging: bool = True,
        project_id: str | None = None,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            use_cloud_logging: Use Google Cloud Logging
            project_id: GCP project ID
        """
        self.name = name
        self.use_cloud_logging = use_cloud_logging
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")

        # Set up standard logger
        self.logger = logging.getLogger(name)

        # Set up cloud logging if enabled
        if use_cloud_logging and self.project_id:
            try:
                logging_client = google_cloud_logging.Client(project=self.project_id)
                self.cloud_logger = logging_client.logger(name)
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Logging: {e}")
                self.cloud_logger = None
        else:
            self.cloud_logger = None

    def log(
        self,
        level: LogLevel,
        message: str,
        context: LogContext | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a structured message.

        Args:
            level: Log level
            message: Log message
            context: Log context
            **kwargs: Additional fields to log
        """
        log_entry = {
            "message": message,
            "level": level.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if context:
            log_entry.update(context.model_dump(exclude_none=True))

        log_entry.update(kwargs)

        # Log to standard logger
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra=log_entry)

        # Log to cloud logger if available
        if self.cloud_logger:
            try:
                severity = level.value
                labels = {}
                if context:
                    if context.agent_name:
                        labels["agent_name"] = context.agent_name
                    if context.operation:
                        labels["operation"] = context.operation

                self.cloud_logger.log_struct(
                    log_entry,
                    severity=severity,
                    labels=labels,
                )
            except Exception as e:
                logger.warning(f"Failed to log to Cloud Logging: {e}")

    def debug(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, context, **kwargs)

    def info(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, context, **kwargs)

    def warning(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, context, **kwargs)

    def error(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, context, **kwargs)

    def critical(self, message: str, context: LogContext | None = None, **kwargs: Any) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, context, **kwargs)


# ============================================================================
# Trace Correlation
# ============================================================================


class TraceContext(BaseModel):
    """Context for distributed tracing."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    operation_name: str
    agent_name: str | None = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: str = "in_progress"
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)


class TraceManager:
    """Manages distributed tracing for multi-agent workflows."""

    def __init__(self, project_id: str | None = None):
        """Initialize trace manager.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.tracer = trace.get_tracer(__name__)
        self.active_traces: dict[str, TraceContext] = {}
        self.lock = threading.Lock()

    def start_trace(
        self,
        operation_name: str,
        agent_name: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TraceContext:
        """Start a new trace.

        Args:
            operation_name: Name of the operation
            agent_name: Name of the agent
            parent_span_id: Parent span ID
            attributes: Initial attributes

        Returns:
            Trace context
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        trace_ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            agent_name=agent_name,
            attributes=attributes or {},
        )

        with self.lock:
            self.active_traces[span_id] = trace_ctx

        logger.debug(
            f"Started trace for {operation_name}",
            extra={"trace_id": trace_id, "span_id": span_id},
        )

        return trace_ctx

    def end_trace(
        self,
        span_id: str,
        status: str = "success",
        error: Exception | None = None,
    ) -> TraceContext | None:
        """End a trace.

        Args:
            span_id: Span ID to end
            status: Final status
            error: Error if failed

        Returns:
            Updated trace context
        """
        with self.lock:
            trace_ctx = self.active_traces.get(span_id)

            if not trace_ctx:
                logger.warning(f"Attempted to end unknown trace: {span_id}")
                return None

            trace_ctx.end_time = datetime.utcnow()
            trace_ctx.duration_ms = (
                trace_ctx.end_time - trace_ctx.start_time
            ).total_seconds() * 1000
            trace_ctx.status = status

            if error:
                trace_ctx.attributes["error"] = str(error)
                trace_ctx.attributes["error_type"] = type(error).__name__

            # Remove from active traces
            del self.active_traces[span_id]

        logger.debug(
            f"Ended trace for {trace_ctx.operation_name}",
            extra={
                "trace_id": trace_ctx.trace_id,
                "span_id": span_id,
                "duration_ms": trace_ctx.duration_ms,
                "status": status,
            },
        )

        return trace_ctx

    def add_event(
        self,
        span_id: str,
        event_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a trace.

        Args:
            span_id: Span ID
            event_name: Event name
            attributes: Event attributes
        """
        with self.lock:
            trace_ctx = self.active_traces.get(span_id)
            if trace_ctx:
                event = {
                    "name": event_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attributes": attributes or {},
                }
                trace_ctx.events.append(event)

    def get_trace_context(self, span_id: str) -> TraceContext | None:
        """Get trace context by span ID.

        Args:
            span_id: Span ID

        Returns:
            Trace context if found
        """
        with self.lock:
            return self.active_traces.get(span_id)


def traced_operation(
    operation_name: str | None = None,
    trace_manager: TraceManager | None = None,
) -> Callable:
    """Decorator to trace function execution.

    Args:
        operation_name: Name of the operation (defaults to function name)
        trace_manager: Trace manager instance

    Returns:
        Decorator function

    Example:
        @traced_operation("process_query")
        def process_query(query: str) -> str:
            return f"Processed: {query}"
    """
    _trace_manager = trace_manager or TraceManager()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            op_name = operation_name or func.__name__

            # Start trace
            trace_ctx = _trace_manager.start_trace(op_name)

            try:
                result = func(*args, **kwargs)
                _trace_manager.end_trace(trace_ctx.span_id, status="success")
                return result
            except Exception as e:
                _trace_manager.end_trace(trace_ctx.span_id, status="error", error=e)
                raise

        return wrapper

    return decorator


# ============================================================================
# Error Reporting and Aggregation
# ============================================================================


class ErrorMetrics(BaseModel):
    """Metrics for error tracking."""

    total_errors: int = 0
    errors_by_category: dict[str, int] = Field(default_factory=dict)
    errors_by_severity: dict[str, int] = Field(default_factory=dict)
    errors_by_agent: dict[str, int] = Field(default_factory=dict)
    recent_errors: list[dict[str, Any]] = Field(default_factory=list)
    error_rate_per_minute: float = 0.0
    last_error_time: datetime | None = None


class ErrorAggregator:
    """Aggregates and tracks errors across the system."""

    def __init__(
        self,
        max_recent_errors: int = 100,
        error_rate_window: int = 60,
    ):
        """Initialize error aggregator.

        Args:
            max_recent_errors: Maximum number of recent errors to keep
            error_rate_window: Window in seconds for calculating error rate
        """
        self.max_recent_errors = max_recent_errors
        self.error_rate_window = error_rate_window
        self.metrics = ErrorMetrics()
        self.error_timestamps: deque[float] = deque()
        self.lock = threading.Lock()

    def record_error(self, error_record: ErrorRecord) -> None:
        """Record an error.

        Args:
            error_record: Error record to track
        """
        with self.lock:
            # Update metrics
            self.metrics.total_errors += 1
            self.metrics.last_error_time = datetime.utcnow()

            error_dict = error_record.error
            category = error_dict.get("category", "unknown")
            severity = error_dict.get("severity", "medium")
            agent_name = error_dict.get("agent_name", "unknown")

            # Update counts by category
            self.metrics.errors_by_category[category] = (
                self.metrics.errors_by_category.get(category, 0) + 1
            )

            # Update counts by severity
            self.metrics.errors_by_severity[severity] = (
                self.metrics.errors_by_severity.get(severity, 0) + 1
            )

            # Update counts by agent
            self.metrics.errors_by_agent[agent_name] = (
                self.metrics.errors_by_agent.get(agent_name, 0) + 1
            )

            # Add to recent errors
            self.metrics.recent_errors.append(error_record.model_dump())
            if len(self.metrics.recent_errors) > self.max_recent_errors:
                self.metrics.recent_errors.pop(0)

            # Track timestamp for rate calculation
            now = time.time()
            self.error_timestamps.append(now)

            # Clean old timestamps
            cutoff = now - self.error_rate_window
            while self.error_timestamps and self.error_timestamps[0] < cutoff:
                self.error_timestamps.popleft()

            # Calculate error rate
            self.metrics.error_rate_per_minute = (
                len(self.error_timestamps) / self.error_rate_window * 60
            )

    def get_metrics(self) -> ErrorMetrics:
        """Get current error metrics.

        Returns:
            Error metrics
        """
        with self.lock:
            return self.metrics.model_copy(deep=True)

    def get_errors_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get errors filtered by category.

        Args:
            category: Error category

        Returns:
            List of errors
        """
        with self.lock:
            return [
                error
                for error in self.metrics.recent_errors
                if error.get("error", {}).get("category") == category
            ]

    def get_errors_by_agent(self, agent_name: str) -> list[dict[str, Any]]:
        """Get errors filtered by agent.

        Args:
            agent_name: Agent name

        Returns:
            List of errors
        """
        with self.lock:
            return [
                error
                for error in self.metrics.recent_errors
                if error.get("error", {}).get("agent_name") == agent_name
            ]

    def reset(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.metrics = ErrorMetrics()
            self.error_timestamps.clear()


# ============================================================================
# Health Checks
# ============================================================================


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a component."""

    name: str
    status: HealthStatus
    message: str | None = None
    last_check: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    """Result of a health check."""

    overall_status: HealthStatus
    components: list[ComponentHealth]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float | None = None


class HealthChecker:
    """Performs health checks on agents and components."""

    def __init__(self):
        """Initialize health checker."""
        self.start_time = time.time()
        self.component_checks: dict[str, Callable[[], ComponentHealth]] = {}
        self.last_check_results: dict[str, ComponentHealth] = {}
        self.lock = threading.Lock()

    def register_check(
        self,
        component_name: str,
        check_func: Callable[[], ComponentHealth],
    ) -> None:
        """Register a health check function.

        Args:
            component_name: Name of the component
            check_func: Function that performs the health check
        """
        with self.lock:
            self.component_checks[component_name] = check_func

    def run_check(self, component_name: str) -> ComponentHealth:
        """Run health check for a component.

        Args:
            component_name: Component name

        Returns:
            Component health status
        """
        check_func = self.component_checks.get(component_name)
        if not check_func:
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                message=f"No health check registered for {component_name}",
            )

        try:
            result = check_func()
            with self.lock:
                self.last_check_results[component_name] = result
            return result
        except Exception as e:
            logger.error(f"Health check failed for {component_name}: {e}")
            result = ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e!s}",
            )
            with self.lock:
                self.last_check_results[component_name] = result
            return result

    def run_all_checks(self) -> HealthCheckResult:
        """Run all registered health checks.

        Returns:
            Overall health check result
        """
        components = []
        for component_name in self.component_checks.keys():
            components.append(self.run_check(component_name))

        # Determine overall status
        if all(c.status == HealthStatus.HEALTHY for c in components):
            overall_status = HealthStatus.HEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        uptime = time.time() - self.start_time

        return HealthCheckResult(
            overall_status=overall_status,
            components=components,
            uptime_seconds=uptime,
        )

    def get_last_results(self) -> dict[str, ComponentHealth]:
        """Get last health check results.

        Returns:
            Dictionary of component health results
        """
        with self.lock:
            return self.last_check_results.copy()


# ============================================================================
# Performance Metrics
# ============================================================================


class PerformanceMetrics(BaseModel):
    """Performance metrics for operations."""

    operation_name: str
    call_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float | None = None
    max_duration_ms: float | None = None
    avg_duration_ms: float = 0.0
    p50_duration_ms: float | None = None
    p95_duration_ms: float | None = None
    p99_duration_ms: float | None = None
    error_count: int = 0
    last_called: datetime | None = None


class MetricsCollector:
    """Collects performance metrics for operations."""

    def __init__(self, max_samples: int = 1000):
        """Initialize metrics collector.

        Args:
            max_samples: Maximum number of samples to keep per operation
        """
        self.max_samples = max_samples
        self.metrics: dict[str, PerformanceMetrics] = {}
        self.samples: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=max_samples))
        self.lock = threading.Lock()

    def record_call(
        self,
        operation_name: str,
        duration_ms: float,
        error: bool = False,
    ) -> None:
        """Record a function call.

        Args:
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            error: Whether the call resulted in an error
        """
        with self.lock:
            if operation_name not in self.metrics:
                self.metrics[operation_name] = PerformanceMetrics(
                    operation_name=operation_name
                )

            metrics = self.metrics[operation_name]
            metrics.call_count += 1
            metrics.total_duration_ms += duration_ms
            metrics.last_called = datetime.utcnow()

            if error:
                metrics.error_count += 1

            # Update min/max
            if metrics.min_duration_ms is None or duration_ms < metrics.min_duration_ms:
                metrics.min_duration_ms = duration_ms
            if metrics.max_duration_ms is None or duration_ms > metrics.max_duration_ms:
                metrics.max_duration_ms = duration_ms

            # Update average
            metrics.avg_duration_ms = metrics.total_duration_ms / metrics.call_count

            # Store sample for percentile calculation
            self.samples[operation_name].append(duration_ms)

            # Calculate percentiles
            samples = sorted(self.samples[operation_name])
            if samples:
                metrics.p50_duration_ms = self._percentile(samples, 50)
                metrics.p95_duration_ms = self._percentile(samples, 95)
                metrics.p99_duration_ms = self._percentile(samples, 99)

    def _percentile(self, sorted_samples: list[float], percentile: float) -> float:
        """Calculate percentile from sorted samples."""
        if not sorted_samples:
            return 0.0
        index = int(len(sorted_samples) * percentile / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def get_metrics(self, operation_name: str | None = None) -> dict[str, PerformanceMetrics]:
        """Get performance metrics.

        Args:
            operation_name: Specific operation name, or None for all

        Returns:
            Dictionary of metrics
        """
        with self.lock:
            if operation_name:
                return {operation_name: self.metrics.get(operation_name)}
            return self.metrics.copy()


def monitor_performance(
    operation_name: str | None = None,
    collector: MetricsCollector | None = None,
) -> Callable:
    """Decorator to monitor function performance.

    Args:
        operation_name: Name of the operation (defaults to function name)
        collector: Metrics collector instance

    Returns:
        Decorator function

    Example:
        @monitor_performance("query_processing")
        def process_query(query: str) -> str:
            return f"Processed: {query}"
    """
    _collector = collector or MetricsCollector()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            op_name = operation_name or func.__name__
            start_time = time.time()
            error = False

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                error = True
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _collector.record_call(op_name, duration_ms, error=error)

        return wrapper

    return decorator

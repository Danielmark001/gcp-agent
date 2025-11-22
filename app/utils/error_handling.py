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
Error Handling Framework for Multi-Agent Architecture

This module provides robust error handling capabilities including:
- Custom exception classes for different error types
- Error recovery strategies for agent failures
- Fallback mechanisms when agents fail
- Retry logic with exponential backoff
"""

import functools
import logging
import random
import time
import traceback
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Custom Exception Classes
# ============================================================================


class AgentErrorSeverity(str, Enum):
    """Severity levels for agent errors."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentErrorCategory(str, Enum):
    """Categories of errors that can occur in the agent system."""

    TOOL_EXECUTION = "tool_execution"
    MODEL_INFERENCE = "model_inference"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    RESOURCE = "resource"
    COMMUNICATION = "communication"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class AgentError(Exception):
    """Base exception for all agent-related errors."""

    def __init__(
        self,
        message: str,
        category: AgentErrorCategory = AgentErrorCategory.UNKNOWN,
        severity: AgentErrorSeverity = AgentErrorSeverity.MEDIUM,
        agent_name: str | None = None,
        recoverable: bool = True,
        original_exception: Exception | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize agent error.

        Args:
            message: Error message
            category: Category of the error
            severity: Severity level of the error
            agent_name: Name of the agent where error occurred
            recoverable: Whether the error is recoverable
            original_exception: The original exception if this wraps another error
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.agent_name = agent_name
        self.recoverable = recoverable
        self.original_exception = original_exception
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        self.traceback_str = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "agent_name": self.agent_name,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "original_exception": (
                str(self.original_exception) if self.original_exception else None
            ),
            "traceback": self.traceback_str,
        }


class ToolExecutionError(AgentError):
    """Error during tool execution."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        tool_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initialize tool execution error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            tool_args: Arguments passed to the tool
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.TOOL_EXECUTION)
        context = kwargs.get("context", {})
        context.update({"tool_name": tool_name, "tool_args": tool_args})
        kwargs["context"] = context
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        self.tool_args = tool_args


class ModelInferenceError(AgentError):
    """Error during model inference."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        prompt: str | None = None,
        **kwargs: Any,
    ):
        """Initialize model inference error.

        Args:
            message: Error message
            model_name: Name of the model that failed
            prompt: Prompt that caused the error
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.MODEL_INFERENCE)
        context = kwargs.get("context", {})
        context.update({"model_name": model_name, "prompt_length": len(prompt) if prompt else 0})
        kwargs["context"] = context
        super().__init__(message, **kwargs)
        self.model_name = model_name


class ValidationError(AgentError):
    """Error during input/output validation."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        invalid_value: Any = None,
        **kwargs: Any,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field_name: Name of the field that failed validation
            invalid_value: The invalid value
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.VALIDATION)
        kwargs.setdefault("recoverable", False)
        context = kwargs.get("context", {})
        context.update({"field_name": field_name, "invalid_value": str(invalid_value)})
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class TimeoutError(AgentError):
    """Error due to operation timeout."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        operation: str | None = None,
        **kwargs: Any,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout threshold that was exceeded
            operation: Operation that timed out
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.TIMEOUT)
        context = kwargs.get("context", {})
        context.update({"timeout_seconds": timeout_seconds, "operation": operation})
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class RateLimitError(AgentError):
    """Error due to rate limiting."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        limit_type: str | None = None,
        **kwargs: Any,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            limit_type: Type of rate limit (e.g., 'requests_per_minute')
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.RATE_LIMIT)
        context = kwargs.get("context", {})
        context.update({"retry_after": retry_after, "limit_type": limit_type})
        kwargs["context"] = context
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ResourceError(AgentError):
    """Error due to resource constraints (memory, disk, etc.)."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        current_usage: float | None = None,
        limit: float | None = None,
        **kwargs: Any,
    ):
        """Initialize resource error.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., 'memory', 'disk')
            current_usage: Current resource usage
            limit: Resource limit
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.RESOURCE)
        kwargs.setdefault("severity", AgentErrorSeverity.HIGH)
        context = kwargs.get("context", {})
        context.update(
            {"resource_type": resource_type, "current_usage": current_usage, "limit": limit}
        )
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class CommunicationError(AgentError):
    """Error during inter-agent communication."""

    def __init__(
        self,
        message: str,
        source_agent: str | None = None,
        target_agent: str | None = None,
        **kwargs: Any,
    ):
        """Initialize communication error.

        Args:
            message: Error message
            source_agent: Name of the source agent
            target_agent: Name of the target agent
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.COMMUNICATION)
        context = kwargs.get("context", {})
        context.update({"source_agent": source_agent, "target_agent": target_agent})
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class ConfigurationError(AgentError):
    """Error due to invalid configuration."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: Any = None,
        **kwargs: Any,
    ):
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that is invalid
            config_value: Invalid configuration value
            **kwargs: Additional arguments passed to AgentError
        """
        kwargs.setdefault("category", AgentErrorCategory.CONFIGURATION)
        kwargs.setdefault("recoverable", False)
        context = kwargs.get("context", {})
        context.update({"config_key": config_key, "config_value": str(config_value)})
        kwargs["context"] = context
        super().__init__(message, **kwargs)


# ============================================================================
# Error Context and Tracking
# ============================================================================


class ErrorContext(BaseModel):
    """Context information for error tracking."""

    error_id: str
    agent_name: str | None = None
    operation: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorRecord(BaseModel):
    """Record of an error occurrence."""

    error: dict[str, Any]
    context: ErrorContext
    recovered: bool = False
    recovery_strategy: str | None = None
    retry_count: int = 0


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,)
    retry_on_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """Calculate delay for exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = min(
        config.initial_delay * (config.exponential_base**attempt),
        config.max_delay,
    )

    if config.jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def retry_with_backoff(
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration
        on_retry: Callback function called on each retry

    Returns:
        Decorated function

    Example:
        @retry_with_backoff(RetryConfig(max_attempts=5))
        def fetch_data():
            # Some operation that might fail
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retry_on_exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff_delay(attempt, config)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for "
                            f"{func.__name__}: {e!s}. Retrying in {delay:.2f}s..."
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}"
                        )

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise AgentError("Retry failed with no exception captured")

        return wrapper

    return decorator


# ============================================================================
# Error Recovery Strategies
# ============================================================================


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    CIRCUIT_BREAKER = "circuit_breaker"


class ErrorRecoveryHandler:
    """Handles error recovery for agent operations."""

    def __init__(
        self,
        fallback_agent: Any | None = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
    ):
        """Initialize error recovery handler.

        Args:
            fallback_agent: Fallback agent to use when primary fails
            circuit_breaker_threshold: Number of failures before opening circuit
            circuit_breaker_timeout: Seconds to wait before resetting circuit
        """
        self.fallback_agent = fallback_agent
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.failure_counts: dict[str, int] = {}
        self.circuit_open_until: dict[str, float] = {}
        self.error_history: list[ErrorRecord] = []

    def is_circuit_open(self, operation: str) -> bool:
        """Check if circuit breaker is open for an operation.

        Args:
            operation: Operation name

        Returns:
            True if circuit is open
        """
        if operation in self.circuit_open_until:
            if time.time() < self.circuit_open_until[operation]:
                return True
            else:
                # Circuit timeout expired, reset
                del self.circuit_open_until[operation]
                self.failure_counts[operation] = 0
        return False

    def record_failure(self, operation: str) -> None:
        """Record a failure for circuit breaker tracking.

        Args:
            operation: Operation name
        """
        self.failure_counts[operation] = self.failure_counts.get(operation, 0) + 1

        if self.failure_counts[operation] >= self.circuit_breaker_threshold:
            self.circuit_open_until[operation] = time.time() + self.circuit_breaker_timeout
            logger.warning(
                f"Circuit breaker opened for {operation} after "
                f"{self.failure_counts[operation]} failures"
            )

    def record_success(self, operation: str) -> None:
        """Record a success to reset failure count.

        Args:
            operation: Operation name
        """
        if operation in self.failure_counts:
            self.failure_counts[operation] = 0

    def handle_error(
        self,
        error: AgentError,
        context: ErrorContext,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
    ) -> ErrorRecord:
        """Handle an error using specified strategy.

        Args:
            error: The error that occurred
            context: Error context
            strategy: Recovery strategy to use

        Returns:
            Error record
        """
        record = ErrorRecord(
            error=error.to_dict(),
            context=context,
            recovery_strategy=strategy.value,
        )

        logger.error(
            f"Error in {context.agent_name or 'unknown'}: {error.message}",
            extra={
                "error_record": record.model_dump(),
                "severity": error.severity.value,
            },
        )

        self.error_history.append(record)

        if strategy == RecoveryStrategy.CIRCUIT_BREAKER and context.operation:
            self.record_failure(context.operation)

        return record

    def recover(
        self,
        func: Callable[..., T],
        error: AgentError,
        context: ErrorContext,
        fallback_func: Callable[..., T] | None = None,
    ) -> T | None:
        """Attempt to recover from an error.

        Args:
            func: Original function to retry
            error: Error that occurred
            context: Error context
            fallback_func: Fallback function to use if recovery fails

        Returns:
            Result of recovery attempt or None
        """
        if not error.recoverable:
            logger.error(f"Error is not recoverable: {error.message}")
            if fallback_func:
                logger.info("Attempting fallback function")
                try:
                    return fallback_func()
                except Exception as e:
                    logger.error(f"Fallback function failed: {e!s}")
            return None

        # Check circuit breaker
        if context.operation and self.is_circuit_open(context.operation):
            logger.warning(f"Circuit breaker is open for {context.operation}")
            if fallback_func:
                return fallback_func()
            return None

        # Attempt retry with backoff
        try:
            config = RetryConfig(max_attempts=3)
            decorated_func = retry_with_backoff(config)(func)
            result = decorated_func()
            if context.operation:
                self.record_success(context.operation)
            return result
        except Exception as e:
            logger.error(f"Recovery failed: {e!s}")
            if context.operation:
                self.record_failure(context.operation)
            if fallback_func:
                return fallback_func()
            return None


# ============================================================================
# Fallback Mechanisms
# ============================================================================


def with_fallback(
    primary_func: Callable[..., T],
    fallback_func: Callable[..., T],
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_fallback: bool = True,
) -> Callable[..., T]:
    """Execute primary function with fallback on error.

    Args:
        primary_func: Primary function to execute
        fallback_func: Fallback function if primary fails
        exceptions: Exceptions that trigger fallback
        log_fallback: Whether to log fallback usage

    Returns:
        Decorated function

    Example:
        result = with_fallback(
            lambda: primary_agent.execute(),
            lambda: fallback_agent.execute(),
        )()
    """

    @functools.wraps(primary_func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return primary_func(*args, **kwargs)
        except exceptions as e:
            if log_fallback:
                logger.warning(
                    f"Primary function {primary_func.__name__} failed: {e!s}. "
                    f"Using fallback {fallback_func.__name__}"
                )
            return fallback_func(*args, **kwargs)

    return wrapper


# ============================================================================
# Safe Execution Wrapper
# ============================================================================


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T | None = None,
    error_handler: ErrorRecoveryHandler | None = None,
    context: ErrorContext | None = None,
    **kwargs: Any,
) -> tuple[T | None, AgentError | None]:
    """Safely execute a function and handle errors.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        default: Default value to return on error
        error_handler: Error recovery handler
        context: Error context
        **kwargs: Keyword arguments for function

    Returns:
        Tuple of (result, error)
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except AgentError as e:
        if error_handler and context:
            error_handler.handle_error(e, context)
        return default, e
    except Exception as e:
        agent_error = AgentError(
            message=f"Unexpected error in {func.__name__}: {e!s}",
            original_exception=e,
        )
        if error_handler and context:
            error_handler.handle_error(agent_error, context)
        return default, agent_error

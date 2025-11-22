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
Validation System for Multi-Agent Architecture

This module provides comprehensive validation capabilities including:
- Input validation for agent tools
- Output validation for agent responses
- Rate limiting and throttling
- Timeout handling for long-running operations
"""

import asyncio
import functools
import logging
import re
import time
from collections import deque
from collections.abc import Callable
from threading import Lock
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from app.utils.error_handling import RateLimitError, TimeoutError, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Input Validation
# ============================================================================


class ToolInputConstraints(BaseModel):
    """Constraints for tool input validation."""

    max_string_length: int = 10000
    max_list_size: int = 1000
    max_dict_size: int = 1000
    max_nesting_depth: int = 10
    allowed_types: list[str] = Field(
        default_factory=lambda: ["str", "int", "float", "bool", "list", "dict", "NoneType"]
    )
    forbidden_patterns: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)


class InputValidator:
    """Validates inputs to agent tools."""

    def __init__(self, constraints: ToolInputConstraints | None = None):
        """Initialize input validator.

        Args:
            constraints: Validation constraints
        """
        self.constraints = constraints or ToolInputConstraints()
        self.forbidden_regex = [
            re.compile(pattern) for pattern in self.constraints.forbidden_patterns
        ]

    def validate_type(self, value: Any, allowed_types: list[str] | None = None) -> None:
        """Validate value type.

        Args:
            value: Value to validate
            allowed_types: List of allowed type names

        Raises:
            ValidationError: If type is not allowed
        """
        allowed_types = allowed_types or self.constraints.allowed_types
        value_type = type(value).__name__

        if value_type not in allowed_types:
            raise ValidationError(
                f"Type {value_type} not allowed. Allowed types: {allowed_types}",
                field_name="type",
                invalid_value=value_type,
            )

    def validate_string(self, value: str, field_name: str = "string") -> None:
        """Validate string input.

        Args:
            value: String to validate
            field_name: Name of the field

        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"Expected string, got {type(value).__name__}",
                field_name=field_name,
                invalid_value=value,
            )

        if len(value) > self.constraints.max_string_length:
            raise ValidationError(
                f"String length {len(value)} exceeds maximum {self.constraints.max_string_length}",
                field_name=field_name,
                invalid_value=f"<string of length {len(value)}>",
            )

        # Check forbidden patterns
        for pattern in self.forbidden_regex:
            if pattern.search(value):
                raise ValidationError(
                    f"String contains forbidden pattern: {pattern.pattern}",
                    field_name=field_name,
                    invalid_value="<redacted>",
                )

    def validate_collection_size(
        self, value: list | dict, field_name: str = "collection"
    ) -> None:
        """Validate collection size.

        Args:
            value: Collection to validate
            field_name: Name of the field

        Raises:
            ValidationError: If collection is too large
        """
        max_size = (
            self.constraints.max_list_size
            if isinstance(value, list)
            else self.constraints.max_dict_size
        )

        if len(value) > max_size:
            raise ValidationError(
                f"Collection size {len(value)} exceeds maximum {max_size}",
                field_name=field_name,
                invalid_value=f"<collection of size {len(value)}>",
            )

    def validate_nesting_depth(
        self, value: Any, max_depth: int | None = None, current_depth: int = 0
    ) -> None:
        """Validate nesting depth of data structures.

        Args:
            value: Value to validate
            max_depth: Maximum allowed nesting depth
            current_depth: Current nesting depth

        Raises:
            ValidationError: If nesting is too deep
        """
        max_depth = max_depth or self.constraints.max_nesting_depth

        if current_depth > max_depth:
            raise ValidationError(
                f"Nesting depth {current_depth} exceeds maximum {max_depth}",
                field_name="nesting_depth",
                invalid_value=current_depth,
            )

        if isinstance(value, dict):
            for _k, v in value.items():
                self.validate_nesting_depth(v, max_depth, current_depth + 1)
        elif isinstance(value, list):
            for item in value:
                self.validate_nesting_depth(item, max_depth, current_depth + 1)

    def validate_required_fields(self, data: dict[str, Any]) -> None:
        """Validate that required fields are present.

        Args:
            data: Data dictionary to validate

        Raises:
            ValidationError: If required fields are missing
        """
        missing_fields = [
            field for field in self.constraints.required_fields if field not in data
        ]

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {missing_fields}",
                field_name="required_fields",
                invalid_value=missing_fields,
            )

    def validate_input(self, data: Any, field_name: str = "input") -> None:
        """Validate input data comprehensively.

        Args:
            data: Data to validate
            field_name: Name of the field

        Raises:
            ValidationError: If validation fails
        """
        # Validate type
        self.validate_type(data)

        # Validate based on type
        if isinstance(data, str):
            self.validate_string(data, field_name)
        elif isinstance(data, (list, dict)):
            self.validate_collection_size(data, field_name)
            self.validate_nesting_depth(data)

        # Validate required fields for dictionaries
        if isinstance(data, dict):
            self.validate_required_fields(data)


def validate_tool_input(constraints: ToolInputConstraints | None = None) -> Callable:
    """Decorator to validate tool inputs.

    Args:
        constraints: Validation constraints

    Returns:
        Decorator function

    Example:
        @validate_tool_input(ToolInputConstraints(max_string_length=1000))
        def my_tool(query: str) -> str:
            return f"Result for {query}"
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        validator = InputValidator(constraints)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Validate all arguments
            for i, arg in enumerate(args):
                try:
                    validator.validate_input(arg, f"arg_{i}")
                except ValidationError as e:
                    logger.error(f"Input validation failed for {func.__name__}: {e.message}")
                    raise

            for key, value in kwargs.items():
                try:
                    validator.validate_input(value, key)
                except ValidationError as e:
                    logger.error(f"Input validation failed for {func.__name__}: {e.message}")
                    raise

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Output Validation
# ============================================================================


class OutputConstraints(BaseModel):
    """Constraints for output validation."""

    max_output_size: int = 100000  # Maximum output size in characters
    required_fields: list[str] = Field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    allow_none: bool = True


class OutputValidator:
    """Validates outputs from agent operations."""

    def __init__(self, constraints: OutputConstraints | None = None):
        """Initialize output validator.

        Args:
            constraints: Validation constraints
        """
        self.constraints = constraints or OutputConstraints()

    def validate_output_size(self, output: Any) -> None:
        """Validate output size.

        Args:
            output: Output to validate

        Raises:
            ValidationError: If output is too large
        """
        output_str = str(output)
        if len(output_str) > self.constraints.max_output_size:
            raise ValidationError(
                f"Output size {len(output_str)} exceeds maximum "
                f"{self.constraints.max_output_size}",
                field_name="output_size",
                invalid_value=len(output_str),
            )

    def validate_output_schema(self, output: dict[str, Any]) -> None:
        """Validate output against schema.

        Args:
            output: Output dictionary to validate

        Raises:
            ValidationError: If output doesn't match schema
        """
        if not self.constraints.output_schema:
            return

        if not isinstance(output, dict):
            raise ValidationError(
                "Output must be a dictionary when schema is specified",
                field_name="output_type",
                invalid_value=type(output).__name__,
            )

        # Check required fields
        for field in self.constraints.required_fields:
            if field not in output:
                raise ValidationError(
                    f"Required output field missing: {field}",
                    field_name="required_fields",
                    invalid_value=field,
                )

    def validate_output(self, output: Any) -> None:
        """Validate output comprehensively.

        Args:
            output: Output to validate

        Raises:
            ValidationError: If validation fails
        """
        if output is None and not self.constraints.allow_none:
            raise ValidationError(
                "Output cannot be None",
                field_name="output",
                invalid_value=None,
            )

        if output is not None:
            self.validate_output_size(output)
            if isinstance(output, dict):
                self.validate_output_schema(output)


def validate_tool_output(constraints: OutputConstraints | None = None) -> Callable:
    """Decorator to validate tool outputs.

    Args:
        constraints: Validation constraints

    Returns:
        Decorator function

    Example:
        @validate_tool_output(OutputConstraints(max_output_size=5000))
        def my_tool(query: str) -> str:
            return f"Result for {query}"
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        validator = OutputValidator(constraints)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)
            try:
                validator.validate_output(result)
            except ValidationError as e:
                logger.error(f"Output validation failed for {func.__name__}: {e.message}")
                raise
            return result

        return wrapper

    return decorator


# ============================================================================
# Rate Limiting
# ============================================================================


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""

    requests_per_second: float | None = None
    requests_per_minute: float | None = None
    requests_per_hour: float | None = None
    burst_size: int = 1  # Number of requests that can burst
    wait_on_limit: bool = True  # Wait or raise error when limit reached


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.lock = Lock()

        # Determine the strictest rate limit
        if config.requests_per_second:
            self.rate = config.requests_per_second
            self.period = 1.0
        elif config.requests_per_minute:
            self.rate = config.requests_per_minute
            self.period = 60.0
        elif config.requests_per_hour:
            self.rate = config.requests_per_hour
            self.period = 3600.0
        else:
            raise ValueError("At least one rate limit must be specified")

        self.tokens = float(config.burst_size)
        self.max_tokens = float(config.burst_size)
        self.last_update = time.time()

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.max_tokens, self.tokens + elapsed * (self.rate / self.period)
        )
        self.last_update = now

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            RateLimitError: If rate limit exceeded and wait_on_limit is False
        """
        with self.lock:
            self._add_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            if not self.config.wait_on_limit:
                wait_time = (tokens - self.tokens) * (self.period / self.rate)
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=wait_time,
                    limit_type=self._get_limit_type(),
                )

            # Wait for tokens to become available
            wait_time = (tokens - self.tokens) * (self.period / self.rate)
            logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.tokens = 0  # Consumed all tokens

    def _get_limit_type(self) -> str:
        """Get the type of rate limit."""
        if self.config.requests_per_second:
            return "requests_per_second"
        elif self.config.requests_per_minute:
            return "requests_per_minute"
        elif self.config.requests_per_hour:
            return "requests_per_hour"
        return "unknown"


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more accurate rate limiting."""

    def __init__(self, config: RateLimitConfig):
        """Initialize sliding window rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.lock = Lock()

        # Determine window size and limit
        if config.requests_per_second:
            self.window_size = 1.0
            self.max_requests = int(config.requests_per_second)
        elif config.requests_per_minute:
            self.window_size = 60.0
            self.max_requests = int(config.requests_per_minute)
        elif config.requests_per_hour:
            self.window_size = 3600.0
            self.max_requests = int(config.requests_per_hour)
        else:
            raise ValueError("At least one rate limit must be specified")

        self.requests: deque[float] = deque()

    def acquire(self) -> None:
        """Acquire permission to make a request.

        Raises:
            RateLimitError: If rate limit exceeded
        """
        with self.lock:
            now = time.time()

            # Remove old requests outside the window
            cutoff = now - self.window_size
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            if len(self.requests) >= self.max_requests:
                if not self.config.wait_on_limit:
                    # Calculate when the oldest request will expire
                    wait_time = self.requests[0] + self.window_size - now
                    raise RateLimitError(
                        f"Rate limit of {self.max_requests} requests per "
                        f"{self.window_size}s exceeded",
                        retry_after=wait_time,
                    )

                # Wait for oldest request to expire
                wait_time = self.requests[0] + self.window_size - now
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)

                # Clean up again after waiting
                now = time.time()
                cutoff = now - self.window_size
                while self.requests and self.requests[0] < cutoff:
                    self.requests.popleft()

            self.requests.append(now)


def rate_limit(config: RateLimitConfig, use_sliding_window: bool = False) -> Callable:
    """Decorator to add rate limiting to functions.

    Args:
        config: Rate limit configuration
        use_sliding_window: Use sliding window instead of token bucket

    Returns:
        Decorator function

    Example:
        @rate_limit(RateLimitConfig(requests_per_second=10))
        def my_function():
            pass
    """
    limiter = (
        SlidingWindowRateLimiter(config) if use_sliding_window else RateLimiter(config)
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            limiter.acquire()
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Timeout Handling
# ============================================================================


def timeout(seconds: float, error_message: str | None = None) -> Callable:
    """Decorator to add timeout to synchronous functions.

    Args:
        seconds: Timeout in seconds
        error_message: Custom error message

    Returns:
        Decorator function

    Example:
        @timeout(30)
        def long_running_function():
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import signal

            def timeout_handler(signum: int, frame: Any) -> None:
                msg = error_message or f"Function {func.__name__} timed out after {seconds}s"
                raise TimeoutError(msg, timeout_seconds=seconds, operation=func.__name__)

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # Restore the old handler and cancel the alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return result

        return wrapper

    return decorator


async def async_timeout(seconds: float, error_message: str | None = None) -> Callable:
    """Decorator to add timeout to async functions.

    Args:
        seconds: Timeout in seconds
        error_message: Custom error message

    Returns:
        Decorator function

    Example:
        @async_timeout(30)
        async def long_running_async_function():
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                msg = error_message or f"Function {func.__name__} timed out after {seconds}s"
                raise TimeoutError(msg, timeout_seconds=seconds, operation=func.__name__) from None

        return wrapper

    return decorator


# ============================================================================
# Combined Validation Decorator
# ============================================================================


def validated_tool(
    input_constraints: ToolInputConstraints | None = None,
    output_constraints: OutputConstraints | None = None,
    rate_limit_config: RateLimitConfig | None = None,
    timeout_seconds: float | None = None,
) -> Callable:
    """Comprehensive validation decorator for tools.

    Args:
        input_constraints: Input validation constraints
        output_constraints: Output validation constraints
        rate_limit_config: Rate limiting configuration
        timeout_seconds: Timeout in seconds

    Returns:
        Decorator function

    Example:
        @validated_tool(
            input_constraints=ToolInputConstraints(max_string_length=1000),
            output_constraints=OutputConstraints(max_output_size=5000),
            rate_limit_config=RateLimitConfig(requests_per_second=10),
            timeout_seconds=30
        )
        def my_tool(query: str) -> str:
            return process_query(query)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply decorators in reverse order (innermost to outermost)
        decorated = func

        if timeout_seconds:
            decorated = timeout(timeout_seconds)(decorated)

        if rate_limit_config:
            decorated = rate_limit(rate_limit_config)(decorated)

        if output_constraints:
            decorated = validate_tool_output(output_constraints)(decorated)

        if input_constraints:
            decorated = validate_tool_input(input_constraints)(decorated)

        return decorated

    return decorator

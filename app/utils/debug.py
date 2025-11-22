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
Debug Utilities for Multi-Agent Architecture

This module provides debugging capabilities including:
- Agent state inspection tools
- Communication log analysis
- Performance profiling utilities
- Debug mode configuration
"""

import cProfile
import functools
import inspect
import io
import json
import logging
import os
import pstats
import sys
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pstats import SortKey
from typing import Any, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Debug Configuration
# ============================================================================


class DebugLevel(str, Enum):
    """Debug verbosity levels."""

    OFF = "off"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"


class DebugConfig(BaseModel):
    """Configuration for debug mode."""

    enabled: bool = False
    level: DebugLevel = DebugLevel.INFO
    log_function_calls: bool = False
    log_function_args: bool = False
    log_function_results: bool = False
    log_exceptions: bool = True
    profile_performance: bool = False
    track_memory: bool = False
    save_debug_logs: bool = False
    debug_log_path: str = "/tmp/agent_debug.log"
    max_log_size_mb: int = 100
    trace_all_operations: bool = False


class DebugManager:
    """Manages debug configuration and state."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "DebugManager":
        """Singleton pattern for debug manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize debug manager."""
        if self._initialized:
            return

        self.config = DebugConfig()
        self._load_config_from_env()
        self._initialized = True

        if self.config.save_debug_logs:
            self._setup_file_logging()

    def _load_config_from_env(self) -> None:
        """Load debug configuration from environment variables."""
        if os.environ.get("AGENT_DEBUG", "").lower() in ("true", "1", "yes"):
            self.config.enabled = True

        debug_level = os.environ.get("AGENT_DEBUG_LEVEL", "").lower()
        if debug_level in [level.value for level in DebugLevel]:
            self.config.level = DebugLevel(debug_level)

        if os.environ.get("AGENT_DEBUG_PROFILE", "").lower() in ("true", "1", "yes"):
            self.config.profile_performance = True

        if os.environ.get("AGENT_DEBUG_TRACE", "").lower() in ("true", "1", "yes"):
            self.config.trace_all_operations = True

    def _setup_file_logging(self) -> None:
        """Set up file logging for debug output."""
        file_handler = logging.FileHandler(self.config.debug_log_path)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    def is_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.config.enabled

    def should_log_level(self, level: DebugLevel) -> bool:
        """Check if a debug level should be logged."""
        if not self.config.enabled:
            return False

        level_order = [
            DebugLevel.OFF,
            DebugLevel.ERROR,
            DebugLevel.WARNING,
            DebugLevel.INFO,
            DebugLevel.DEBUG,
            DebugLevel.TRACE,
        ]

        return level_order.index(level) <= level_order.index(self.config.level)

    def set_config(self, **kwargs: Any) -> None:
        """Update debug configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# ============================================================================
# Agent State Inspection
# ============================================================================


class AgentStateSnapshot(BaseModel):
    """Snapshot of agent state at a point in time."""

    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state_variables: dict[str, Any] = Field(default_factory=dict)
    active_operations: list[str] = Field(default_factory=list)
    memory_usage_mb: float | None = None
    thread_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentStateInspector:
    """Inspects and tracks agent state."""

    def __init__(self):
        """Initialize state inspector."""
        self.snapshots: dict[str, deque[AgentStateSnapshot]] = defaultdict(
            lambda: deque(maxlen=100)
        )
        self.lock = threading.Lock()

    def capture_snapshot(
        self,
        agent_name: str,
        state_vars: dict[str, Any] | None = None,
        active_ops: list[str] | None = None,
    ) -> AgentStateSnapshot:
        """Capture a snapshot of agent state.

        Args:
            agent_name: Name of the agent
            state_vars: State variables to capture
            active_ops: List of active operations

        Returns:
            State snapshot
        """
        import psutil

        process = psutil.Process()

        snapshot = AgentStateSnapshot(
            agent_name=agent_name,
            state_variables=state_vars or {},
            active_operations=active_ops or [],
            memory_usage_mb=process.memory_info().rss / 1024 / 1024,
            thread_count=process.num_threads(),
        )

        with self.lock:
            self.snapshots[agent_name].append(snapshot)

        return snapshot

    def get_snapshots(
        self,
        agent_name: str,
        limit: int | None = None,
    ) -> list[AgentStateSnapshot]:
        """Get state snapshots for an agent.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots
        """
        with self.lock:
            snapshots = list(self.snapshots.get(agent_name, []))
            if limit:
                snapshots = snapshots[-limit:]
            return snapshots

    def get_latest_snapshot(self, agent_name: str) -> AgentStateSnapshot | None:
        """Get the latest snapshot for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Latest snapshot or None
        """
        with self.lock:
            snapshots = self.snapshots.get(agent_name)
            return snapshots[-1] if snapshots else None

    def compare_snapshots(
        self,
        snapshot1: AgentStateSnapshot,
        snapshot2: AgentStateSnapshot,
    ) -> dict[str, Any]:
        """Compare two snapshots.

        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot

        Returns:
            Comparison results
        """
        return {
            "time_diff_seconds": (
                snapshot2.timestamp - snapshot1.timestamp
            ).total_seconds(),
            "memory_diff_mb": (
                (snapshot2.memory_usage_mb or 0) - (snapshot1.memory_usage_mb or 0)
            ),
            "thread_diff": (
                (snapshot2.thread_count or 0) - (snapshot1.thread_count or 0)
            ),
            "state_changes": self._diff_dicts(
                snapshot1.state_variables, snapshot2.state_variables
            ),
        }

    def _diff_dicts(
        self,
        dict1: dict[str, Any],
        dict2: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate difference between two dictionaries."""
        changes = {}

        # Find added/modified keys
        for key, value2 in dict2.items():
            if key not in dict1:
                changes[key] = {"status": "added", "new_value": value2}
            elif dict1[key] != value2:
                changes[key] = {
                    "status": "modified",
                    "old_value": dict1[key],
                    "new_value": value2,
                }

        # Find removed keys
        for key in dict1:
            if key not in dict2:
                changes[key] = {"status": "removed", "old_value": dict1[key]}

        return changes


# ============================================================================
# Communication Log Analysis
# ============================================================================


class MessageType(str, Enum):
    """Types of inter-agent messages."""

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class CommunicationLog(BaseModel):
    """Log entry for inter-agent communication."""

    log_id: str = Field(default_factory=lambda: str(time.time_ns()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: MessageType
    source_agent: str
    target_agent: str | None = None
    operation: str
    payload: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] | None = None
    duration_ms: float | None = None
    success: bool = True
    error_message: str | None = None


class CommunicationLogger:
    """Logs and analyzes inter-agent communication."""

    def __init__(self, max_logs: int = 10000):
        """Initialize communication logger.

        Args:
            max_logs: Maximum number of logs to keep
        """
        self.max_logs = max_logs
        self.logs: deque[CommunicationLog] = deque(maxlen=max_logs)
        self.lock = threading.Lock()

    def log_message(
        self,
        message_type: MessageType,
        source_agent: str,
        operation: str,
        target_agent: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CommunicationLog:
        """Log a communication message.

        Args:
            message_type: Type of message
            source_agent: Source agent name
            operation: Operation being performed
            target_agent: Target agent name
            payload: Message payload

        Returns:
            Communication log entry
        """
        log_entry = CommunicationLog(
            message_type=message_type,
            source_agent=source_agent,
            target_agent=target_agent,
            operation=operation,
            payload=payload or {},
        )

        with self.lock:
            self.logs.append(log_entry)

        return log_entry

    def update_response(
        self,
        log_id: str,
        response: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Update a log entry with response information.

        Args:
            log_id: Log entry ID
            response: Response data
            duration_ms: Operation duration
            success: Whether operation succeeded
            error_message: Error message if failed
        """
        with self.lock:
            for log in self.logs:
                if log.log_id == log_id:
                    log.response = response
                    log.duration_ms = duration_ms
                    log.success = success
                    log.error_message = error_message
                    break

    def get_logs(
        self,
        source_agent: str | None = None,
        target_agent: str | None = None,
        message_type: MessageType | None = None,
        limit: int | None = None,
    ) -> list[CommunicationLog]:
        """Get filtered communication logs.

        Args:
            source_agent: Filter by source agent
            target_agent: Filter by target agent
            message_type: Filter by message type
            limit: Maximum number of logs to return

        Returns:
            Filtered logs
        """
        with self.lock:
            logs = list(self.logs)

        # Apply filters
        if source_agent:
            logs = [log for log in logs if log.source_agent == source_agent]
        if target_agent:
            logs = [log for log in logs if log.target_agent == target_agent]
        if message_type:
            logs = [log for log in logs if log.message_type == message_type]

        # Apply limit
        if limit:
            logs = logs[-limit:]

        return logs

    def analyze_communication_patterns(self) -> dict[str, Any]:
        """Analyze communication patterns.

        Returns:
            Analysis results
        """
        with self.lock:
            logs = list(self.logs)

        if not logs:
            return {"message": "No communication logs available"}

        total_messages = len(logs)
        successful_messages = sum(1 for log in logs if log.success)
        failed_messages = total_messages - successful_messages

        # Calculate average duration
        durations = [log.duration_ms for log in logs if log.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Count messages by type
        messages_by_type = defaultdict(int)
        for log in logs:
            messages_by_type[log.message_type.value] += 1

        # Count messages by agent pair
        agent_pairs = defaultdict(int)
        for log in logs:
            if log.target_agent:
                pair = f"{log.source_agent} -> {log.target_agent}"
                agent_pairs[pair] += 1

        return {
            "total_messages": total_messages,
            "successful_messages": successful_messages,
            "failed_messages": failed_messages,
            "success_rate": successful_messages / total_messages if total_messages > 0 else 0,
            "average_duration_ms": avg_duration,
            "messages_by_type": dict(messages_by_type),
            "most_active_agent_pairs": dict(
                sorted(agent_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }

    def export_logs(self, filepath: str) -> None:
        """Export logs to a file.

        Args:
            filepath: Path to export file
        """
        with self.lock:
            logs = [log.model_dump() for log in self.logs]

        with open(filepath, "w") as f:
            json.dump(logs, f, indent=2, default=str)

        logger.info(f"Exported {len(logs)} communication logs to {filepath}")


# ============================================================================
# Performance Profiling
# ============================================================================


class ProfileResult(BaseModel):
    """Result of a performance profile."""

    function_name: str
    total_time: float
    num_calls: int
    time_per_call: float
    cumulative_time: float
    top_functions: list[dict[str, Any]] = Field(default_factory=list)


class PerformanceProfiler:
    """Profiles function performance."""

    def __init__(self):
        """Initialize performance profiler."""
        self.profiles: dict[str, cProfile.Profile] = {}
        self.results: dict[str, ProfileResult] = {}
        self.lock = threading.Lock()

    def start_profiling(self, profile_name: str) -> None:
        """Start profiling.

        Args:
            profile_name: Name for this profile
        """
        with self.lock:
            profiler = cProfile.Profile()
            profiler.enable()
            self.profiles[profile_name] = profiler

    def stop_profiling(self, profile_name: str) -> ProfileResult | None:
        """Stop profiling and get results.

        Args:
            profile_name: Name of the profile

        Returns:
            Profile results
        """
        with self.lock:
            profiler = self.profiles.get(profile_name)
            if not profiler:
                logger.warning(f"No active profile found: {profile_name}")
                return None

            profiler.disable()

            # Get statistics
            string_io = io.StringIO()
            stats = pstats.Stats(profiler, stream=string_io)
            stats.sort_stats(SortKey.CUMULATIVE)

            # Extract top functions
            top_functions = []
            for func, (_cc, nc, tt, ct, _callers) in list(stats.stats.items())[:20]:
                top_functions.append({
                    "function": f"{func[0]}:{func[1]}:{func[2]}",
                    "calls": nc,
                    "total_time": tt,
                    "cumulative_time": ct,
                    "time_per_call": tt / nc if nc > 0 else 0,
                })

            result = ProfileResult(
                function_name=profile_name,
                total_time=stats.total_tt,
                num_calls=stats.total_calls,
                time_per_call=stats.total_tt / stats.total_calls if stats.total_calls > 0 else 0,
                cumulative_time=stats.total_tt,
                top_functions=top_functions,
            )

            self.results[profile_name] = result
            del self.profiles[profile_name]

            return result

    def get_result(self, profile_name: str) -> ProfileResult | None:
        """Get a saved profile result.

        Args:
            profile_name: Name of the profile

        Returns:
            Profile result if available
        """
        return self.results.get(profile_name)


def profile_function(profile_name: str | None = None) -> Callable:
    """Decorator to profile a function.

    Args:
        profile_name: Name for the profile (defaults to function name)

    Returns:
        Decorator function

    Example:
        @profile_function("process_query")
        def process_query(query: str) -> str:
            return f"Processed: {query}"
    """
    profiler = PerformanceProfiler()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            name = profile_name or func.__name__

            profiler.start_profiling(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                profile_result = profiler.stop_profiling(name)
                if profile_result:
                    logger.debug(f"Profile for {name}: {profile_result.model_dump()}")

        return wrapper

    return decorator


# ============================================================================
# Debug Decorators
# ============================================================================


def debug_trace(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to trace function execution in debug mode.

    Args:
        func: Function to trace

    Returns:
        Decorated function

    Example:
        @debug_trace
        def my_function(x: int) -> int:
            return x * 2
    """
    debug_manager = DebugManager()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not debug_manager.is_enabled():
            return func(*args, **kwargs)

        func_name = f"{func.__module__}.{func.__qualname__}"
        start_time = time.time()

        if debug_manager.should_log_level(DebugLevel.DEBUG):
            args_repr = ""
            if debug_manager.config.log_function_args:
                args_repr = f" with args={args}, kwargs={kwargs}"
            logger.debug(f"Entering {func_name}{args_repr}")

        try:
            result = func(*args, **kwargs)

            if debug_manager.should_log_level(DebugLevel.DEBUG):
                duration_ms = (time.time() - start_time) * 1000
                result_repr = ""
                if debug_manager.config.log_function_results:
                    result_repr = f" -> {result}"
                logger.debug(
                    f"Exiting {func_name} ({duration_ms:.2f}ms){result_repr}"
                )

            return result
        except Exception as e:
            if debug_manager.config.log_exceptions:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Exception in {func_name} ({duration_ms:.2f}ms): {e}",
                    exc_info=True,
                )
            raise

    return wrapper


def debug_inspect(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to inspect function arguments and return values.

    Args:
        func: Function to inspect

    Returns:
        Decorated function
    """
    debug_manager = DebugManager()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not debug_manager.is_enabled():
            return func(*args, **kwargs)

        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        if debug_manager.should_log_level(DebugLevel.TRACE):
            logger.debug(f"Function: {func.__name__}")
            logger.debug(f"Arguments: {bound_args.arguments}")

        result = func(*args, **kwargs)

        if debug_manager.should_log_level(DebugLevel.TRACE):
            logger.debug(f"Return value: {result}")
            logger.debug(f"Return type: {type(result).__name__}")

        return result

    return wrapper


# ============================================================================
# Debug Utilities
# ============================================================================


def print_agent_state(agent: Any, verbose: bool = False) -> None:
    """Print the current state of an agent.

    Args:
        agent: Agent to inspect
        verbose: Include detailed information
    """
    print(f"\n{'=' * 60}")
    print(f"Agent State: {getattr(agent, 'name', 'Unknown')}")
    print(f"{'=' * 60}")

    # Print agent attributes
    for attr_name in dir(agent):
        if attr_name.startswith("_"):
            continue

        try:
            attr_value = getattr(agent, attr_name)
            if callable(attr_value):
                if verbose:
                    print(f"  {attr_name}(): <method>")
            else:
                print(f"  {attr_name}: {attr_value}")
        except Exception as e:
            print(f"  {attr_name}: <error accessing: {e}>")

    print(f"{'=' * 60}\n")


def dump_debug_info(filepath: str) -> None:
    """Dump all debug information to a file.

    Args:
        filepath: Path to dump file
    """
    debug_manager = DebugManager()

    debug_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "config": debug_manager.config.model_dump(),
        "python_version": sys.version,
        "platform": sys.platform,
    }

    with open(filepath, "w") as f:
        json.dump(debug_info, f, indent=2, default=str)

    logger.info(f"Debug information dumped to {filepath}")


def enable_debug_mode(
    level: DebugLevel = DebugLevel.DEBUG,
    **kwargs: Any,
) -> None:
    """Enable debug mode with specified configuration.

    Args:
        level: Debug level
        **kwargs: Additional configuration options
    """
    debug_manager = DebugManager()
    debug_manager.set_config(enabled=True, level=level, **kwargs)
    logger.info(f"Debug mode enabled with level: {level.value}")


def disable_debug_mode() -> None:
    """Disable debug mode."""
    debug_manager = DebugManager()
    debug_manager.set_config(enabled=False)
    logger.info("Debug mode disabled")

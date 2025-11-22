# Testing Infrastructure for Multi-Agent System

This directory contains comprehensive testing infrastructure for the multi-agent system built with Google's Agent Development Kit (ADK).

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Utilities](#test-utilities)
- [Writing New Tests](#writing-new-tests)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Overview

The testing infrastructure is designed to ensure reliability, performance, and correctness of the multi-agent system. It covers:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Agent interaction and coordination testing
- **End-to-End Tests**: Complete workflow testing
- **Load Tests**: Performance and scalability testing

## Test Structure

```
tests/
├── conftest.py                 # Global pytest fixtures and configuration
├── utils/                      # Test utilities and helpers
│   ├── __init__.py
│   ├── mocks.py               # Mock objects for testing
│   ├── helpers.py             # Helper functions
│   └── data_generators.py    # Test data generators
├── unit/                      # Unit tests
│   ├── test_agent_tools.py
│   ├── test_gcs_utils.py
│   ├── test_typing.py
│   ├── test_tracing.py
│   ├── test_agent_engine_app_unit.py
│   └── test_dummy.py
├── integration/               # Integration tests
│   ├── test_agent.py
│   ├── test_agent_engine_app.py
│   ├── test_agent_coordination.py
│   └── test_error_handling.py
├── e2e/                       # End-to-end tests
│   ├── test_complete_workflows.py
│   └── test_multi_agent_scenarios.py
└── load_test/                 # Load and performance tests
    ├── load_test.py
    ├── multi_agent_load_test.py
    └── performance_test.py
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on individual components in isolation.

**Coverage:**
- Agent tool functions (`get_weather`, `get_current_time`)
- GCS utilities (`create_bucket_if_not_exists`)
- Type models (`Feedback`)
- Tracing utilities (`CloudTraceLoggingSpanExporter`)
- Agent configuration

**Example:**
```python
def test_san_francisco_weather() -> None:
    """Test weather for San Francisco returns foggy."""
    result = get_weather("San Francisco")
    assert "60 degrees" in result
    assert "foggy" in result
```

**Run unit tests:**
```bash
pytest tests/unit/ -v
```

### Integration Tests (`tests/integration/`)

Integration tests verify that multiple components work together correctly.

**Coverage:**
- Agent streaming functionality
- Multi-turn conversations
- Session management
- Feedback registration
- Error handling
- Edge cases

**Example:**
```python
def test_sequential_queries_same_session() -> None:
    """Test multiple queries in the same session."""
    session_service = InMemorySessionService()
    session = session_service.create_session(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")
    # ... execute multiple queries
```

**Run integration tests:**
```bash
pytest tests/integration/ -v
```

### End-to-End Tests (`tests/e2e/`)

E2E tests validate complete user workflows from start to finish.

**Coverage:**
- Complete conversation workflows
- Multi-user scenarios
- Concurrent operations
- Feedback submission workflows
- Session lifecycle
- Complex multi-part queries

**Example:**
```python
def test_multi_turn_conversation_workflow() -> None:
    """Test complete workflow for multi-turn conversation."""
    # Create session, send multiple messages, verify responses
```

**Run e2e tests:**
```bash
pytest tests/e2e/ -v
```

### Load Tests (`tests/load_test/`)

Load tests assess system performance under various load conditions.

**Coverage:**
- Single user query performance
- Multi-user concurrent queries
- Burst traffic patterns
- Long-running queries
- Throughput metrics
- Response time analysis

**Types of load tests:**

1. **Basic Load Test** (`load_test.py`):
   - Single query pattern
   - Measures baseline performance

2. **Multi-Agent Load Test** (`multi_agent_load_test.py`):
   - Different user types (MultiAgentUser, BurstTrafficUser, LongRunningQueryUser)
   - Varied query patterns
   - Simulates realistic traffic

3. **Performance Test** (`performance_test.py`):
   - Response time metrics
   - Throughput analysis
   - Memory stability
   - Concurrent session performance

**Run load tests with Locust:**
```bash
# For deployed agent
locust -f tests/load_test/multi_agent_load_test.py

# Access web UI at http://localhost:8089
```

**Run performance tests with pytest:**
```bash
pytest tests/load_test/performance_test.py -v -s
```

## Test Utilities

### Fixtures (`conftest.py`)

Global pytest fixtures available to all tests:

- `setup_test_environment`: Sets up environment variables
- `mock_google_auth`: Mocks Google authentication
- `mock_vertexai`: Mocks Vertex AI initialization
- `mock_storage_client`: Mocks GCS client
- `mock_logging_client`: Mocks Cloud Logging client
- `test_agent`: Provides a test agent instance
- `agent_app`: Provides an AgentEngineApp instance
- `session_service`: Provides InMemorySessionService
- `sample_weather_queries`: Sample weather queries
- `sample_feedback_data`: Sample feedback data

### Mock Objects (`tests/utils/mocks.py`)

Reusable mock objects for testing:

- `MockAgentResponse`: Mock agent response
- `MockStorageClient`: Mock GCS client
- `MockBucket`: Mock GCS bucket
- `MockBlob`: Mock GCS blob
- `MockCloudLoggingClient`: Mock logging client
- `MockLogger`: Mock logger
- `MockSpan`: Mock OpenTelemetry span
- `create_mock_agent()`: Create mock agent
- `create_mock_session()`: Create mock session
- `create_mock_event()`: Create mock event

### Helper Functions (`tests/utils/helpers.py`)

Utility functions for test assertions and operations:

- `extract_text_from_events()`: Extract text from event lists
- `assert_valid_agent_response()`: Assert valid agent response
- `wait_for_condition()`: Wait for a condition to be met
- `compare_agent_states()`: Compare agent states
- `validate_feedback_structure()`: Validate feedback data
- `count_tool_calls()`: Count tool calls in events
- `measure_response_time()`: Measure function execution time

### Data Generators (`tests/utils/data_generators.py`)

Generate test data dynamically:

- `generate_random_query()`: Generate random queries
- `generate_session_data()`: Generate session data
- `generate_feedback_data()`: Generate feedback data
- `generate_mock_events()`: Generate mock events
- `generate_agent_config()`: Generate agent configuration
- `generate_error_scenarios()`: Generate error test cases
- `generate_load_test_scenarios()`: Generate load test scenarios
- `generate_concurrent_agent_requests()`: Generate concurrent requests
- `generate_edge_case_inputs()`: Generate edge case inputs

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Performance tests
pytest tests/load_test/performance_test.py -v -s
```

### Run Specific Test Files

```bash
pytest tests/unit/test_agent_tools.py -v
```

### Run Specific Test Functions

```bash
pytest tests/unit/test_agent_tools.py::TestGetWeatherTool::test_san_francisco_weather -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run Load Tests

```bash
# Using Locust (requires deployed agent)
locust -f tests/load_test/multi_agent_load_test.py

# Specify users and duration
locust -f tests/load_test/multi_agent_load_test.py --users 10 --spawn-rate 2 --run-time 1m --headless
```

## Writing New Tests

### Unit Test Template

```python
# tests/unit/test_my_component.py
from app.my_module import my_function

class TestMyComponent:
    """Tests for my component."""

    def test_basic_functionality(self) -> None:
        """Test basic functionality."""
        result = my_function("input")
        assert result == "expected_output"

    def test_edge_case(self) -> None:
        """Test edge case handling."""
        result = my_function("")
        assert result is not None
```

### Integration Test Template

```python
# tests/integration/test_my_integration.py
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agent import root_agent

def test_my_integration() -> None:
    """Test integration between components."""
    session_service = InMemorySessionService()
    session = session_service.create_session(user_id="test", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Execute test logic
    # ...

    # Assert results
    assert result is not None
```

### E2E Test Template

```python
# tests/e2e/test_my_workflow.py
def test_complete_workflow() -> None:
    """Test complete user workflow."""
    # Setup
    # Execute workflow steps
    # Verify final state
    pass
```

## Best Practices

### 1. Test Naming

- Use descriptive test names: `test_weather_query_for_san_francisco`
- Group related tests in classes: `TestWeatherTool`
- Use docstrings to explain what the test does

### 2. Test Isolation

- Each test should be independent
- Use fixtures for common setup
- Clean up resources after tests
- Don't rely on test execution order

### 3. Assertions

- Use specific assertions: `assert value == expected` not `assert value`
- Include helpful error messages: `assert value == expected, f"Got {value}"`
- Test both positive and negative cases

### 4. Mocking

- Mock external dependencies (GCS, Cloud Logging, etc.)
- Use provided mock utilities from `tests/utils/mocks.py`
- Don't mock the code under test

### 5. Test Data

- Use data generators for dynamic test data
- Keep test data realistic but minimal
- Don't hardcode large test data in tests

### 6. Performance Tests

- Set reasonable timeout thresholds
- Test performance regression, not absolute values
- Run performance tests in consistent environments

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Running Tests in Docker

```bash
docker build -t agent-tests .
docker run agent-tests pytest tests/ -v
```

## Test Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Cover all major workflows
- **E2E Tests**: Cover critical user journeys
- **Load Tests**: Establish performance baselines

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `PYTHONPATH` includes project root
   - Install package in development mode: `pip install -e .`

2. **Authentication Errors**
   - Mock external services using provided fixtures
   - Set `GOOGLE_CLOUD_PROJECT` environment variable

3. **Timeout Errors**
   - Increase timeout values in tests
   - Use `pytest --timeout=60` for global timeout

4. **Flaky Tests**
   - Increase wait times in async operations
   - Use `wait_for_condition()` helper for polling

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Google ADK Documentation](https://github.com/googleapis/python-adk)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Contributing

When adding new tests:

1. Follow the existing structure and naming conventions
2. Add appropriate docstrings
3. Use provided utilities and fixtures
4. Ensure tests are isolated and repeatable
5. Update this README if adding new test categories

## Support

For questions or issues with tests:
- Check existing test examples
- Review pytest output for detailed error messages
- Consult the test utilities documentation

# Multi-Agent System Architecture

## Overview

This GCP Agent project now features a sophisticated multi-agent system that enables complex task orchestration through specialized agents. Each agent is designed for specific capabilities, and they work together under the coordination of a central orchestrator.

## Architecture Design

### Core Components

1. **Coordinator Agent** - Orchestrates tasks across specialized agents
2. **Research Agent** - Gathers information and conducts research
3. **Code Generation Agent** - Writes, reviews, and refactors code
4. **Data Analysis Agent** - Processes and analyzes data

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Coordinator Agent                           │
│  • Analyzes requests                                         │
│  • Delegates to specialized agents                           │
│  • Synthesizes results                                       │
└─────┬───────────┬────────────┬─────────────┬────────────────┘
      │           │            │             │
      ▼           ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Research │ │   Code   │ │   Data   │ │  Future  │
│  Agent   │ │   Gen    │ │ Analysis │ │  Agents  │
│          │ │  Agent   │ │  Agent   │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              State Manager                                   │
│  • Inter-agent communication                                 │
│  • Shared state management                                   │
│  • Task coordination                                         │
└─────────────────────────────────────────────────────────────┘
```

## Agent Capabilities

### Coordinator Agent

**Purpose**: Central orchestrator for the multi-agent system

**Key Features**:
- Task analysis and decomposition
- Agent delegation and load balancing
- Result synthesis and aggregation
- Error handling and recovery

**Tools**:
- `delegate_task(agent_name, task, context)` - Delegate tasks to specialized agents
- `get_agent_status(agent_name)` - Check agent status
- `get_agent_results(agent_name)` - Retrieve agent results
- `get_all_agents_status()` - Get system-wide status
- `synthesize_results(agent_names, synthesis_prompt)` - Combine results

### Research Agent

**Purpose**: Information gathering and research

**Key Features**:
- Web search simulation (ready for real API integration)
- Information gathering from multiple sources
- Fact verification and validation
- Research synthesis and reporting

**Tools**:
- `web_search(query, num_results)` - Search for information
- `gather_information(topic, sources)` - Comprehensive research
- `verify_information(claim, sources)` - Fact checking
- `synthesize_research(topic, key_points)` - Create research summaries
- `get_current_knowledge(topic)` - Access knowledge base

### Code Generation Agent

**Purpose**: Code writing, review, and refactoring

**Key Features**:
- Multi-language code generation
- Code quality and security review
- Unit test generation
- Code refactoring and optimization
- Code explanation and documentation

**Supported Languages**: Python, JavaScript, TypeScript, Go, Java

**Tools**:
- `generate_code(language, description, requirements)` - Generate code
- `review_code(code, language, focus_areas)` - Code review
- `generate_tests(code, language, test_framework)` - Create unit tests
- `refactor_code(code, language, goals)` - Refactor code
- `explain_code(code, language, detail_level)` - Explain code

### Data Analysis Agent

**Purpose**: Data processing and analysis

**Key Features**:
- Dataset analysis and insights
- Statistical analysis
- Pattern and trend identification
- Data visualization specifications
- Data cleaning and preprocessing
- Report generation

**Supported Formats**: CSV, JSON, Parquet, Excel

**Tools**:
- `analyze_dataset(data_description, analysis_type, columns)` - Analyze data
- `perform_statistical_analysis(data_description, tests, confidence_level)` - Stats
- `identify_patterns(data_description, pattern_type)` - Find patterns
- `generate_visualization(data_description, viz_type, title)` - Create viz specs
- `clean_data(data_description, cleaning_operations)` - Data cleaning
- `generate_report(analysis_summary, include_sections)` - Create reports

## State Management

### StateManager Class

The `StateManager` provides thread-safe state management and inter-agent communication:

**Features**:
- Agent state tracking (idle, working, completed, error)
- Inter-agent messaging
- Global context sharing
- Result aggregation

**Key Methods**:
- `register_agent(agent_name)` - Register new agent
- `set(agent_name, key, value)` - Set agent state
- `get(agent_name, key)` - Get agent state
- `send_message(from_agent, to_agent, content)` - Send message
- `get_messages(agent_name)` - Retrieve messages
- `set_global_context(key, value)` - Set global context
- `get_agent_state(agent_name)` - Get complete agent state

## Configuration System

### AgentConfig Class

Located in `/home/user/gcp-agent/app/config/agent_config.py`

**Configuration Options**:

```python
# Model configuration
default_model: str = "gemini-2.0-flash"
coordinator_model: str = "gemini-2.0-flash"
research_model: str = "gemini-2.0-flash"
code_gen_model: str = "gemini-2.0-flash"
data_analysis_model: str = "gemini-2.0-flash"

# Behavior configuration
max_iterations: int = 10
timeout_seconds: int = 300
enable_parallel_execution: bool = True

# Agent-specific configuration
research_max_search_results: int = 10
research_enable_web_search: bool = True
code_gen_supported_languages: list[str]
data_analysis_max_dataset_size: int = 1000000
data_analysis_supported_formats: list[str]

# Communication configuration
enable_inter_agent_messages: bool = True
message_queue_size: int = 100
```

**Environment Variable Support**:
- `AGENT_DEFAULT_MODEL` - Default model for all agents
- `AGENT_MAX_ITERATIONS` - Maximum iterations
- `AGENT_TIMEOUT_SECONDS` - Timeout in seconds
- `AGENT_ENABLE_PARALLEL` - Enable parallel execution
- `RESEARCH_ENABLE_WEB_SEARCH` - Enable web search
- `CODE_GEN_ENABLE_VALIDATION` - Enable code validation

## Agent Registry and Factory Pattern

### AgentRegistry Class

Located in `/home/user/gcp-agent/app/agents/registry.py`

**Purpose**: Centralized agent creation and management

**Key Methods**:
- `create_agent(agent_type, **kwargs)` - Create new agent
- `get_agent(agent_name)` - Retrieve agent by name
- `get_all_agents()` - Get all registered agents
- `create_multi_agent_system()` - Initialize complete system
- `get_agent_types()` - List available agent types
- `reset_all_agents()` - Reset the system

**Agent Types** (use as constants):
- `AgentRegistry.COORDINATOR`
- `AgentRegistry.RESEARCH`
- `AgentRegistry.CODE_GENERATION`
- `AgentRegistry.DATA_ANALYSIS`

## Usage Examples

### Basic Usage (Backward Compatible)

The existing `root_agent` in `app/agent.py` now includes multi-agent capabilities:

```python
from app.agent import root_agent

# Use as before - the agent now has coordinator capabilities
response = root_agent.query("What's the weather in San Francisco?")
```

### Using the Multi-Agent System

```python
from app.agent import (
    get_coordinator,
    get_specialized_agent,
    get_all_agents,
    get_agent_registry_instance
)

# Get the coordinator
coordinator = get_coordinator()

# Orchestrate a complex task
result = coordinator.orchestrate(
    user_query="Research Python best practices and generate example code",
    context={"language": "python", "topic": "best practices"}
)

# Get a specific specialized agent
research_agent = get_specialized_agent("research_agent")

# Get all agents
all_agents = get_all_agents()
```

### Creating Custom Agent Configurations

```python
from app.agents.registry import AgentRegistry
from app.config.agent_config import AgentConfig
from app.agents.state_manager import StateManager

# Custom configuration
config = AgentConfig(
    default_model="gemini-2.0-flash",
    max_iterations=20,
    research_enable_web_search=True,
    code_gen_supported_languages=["python", "go"]
)

# Create registry with custom config
state_manager = StateManager()
registry = AgentRegistry(config=config, state_manager=state_manager)

# Create multi-agent system
coordinator = registry.create_multi_agent_system()
```

### Direct Agent Creation

```python
from app.agents.registry import AgentRegistry

registry = AgentRegistry()

# Create individual agents
research_agent = registry.create_agent(AgentRegistry.RESEARCH)
code_agent = registry.create_agent(AgentRegistry.CODE_GENERATION)
data_agent = registry.create_agent(AgentRegistry.DATA_ANALYSIS)

# Use the agents directly
research_agent.execute_task(
    task="Research machine learning frameworks",
    context={"focus": "python"}
)
```

## Integration with Existing Infrastructure

### With AgentEngineApp

The multi-agent system integrates seamlessly with the existing `AgentEngineApp`:

```python
from app.agent_engine_app import AgentEngineApp
from app.agent import root_agent

# The root_agent now includes multi-agent capabilities
agent_engine = AgentEngineApp(agent=root_agent)
```

### Deployment

The deployment process remains the same:

```bash
# Deploy to Vertex AI
make backend

# Or use the deployment script
python -m app.agent_engine_app \
    --project your-project-id \
    --location us-central1 \
    --agent-name my-multi-agent
```

## File Structure

```
app/
├── agent.py                          # Main agent with multi-agent integration
├── agent_engine_app.py               # Agent Engine application
├── agents/                           # Multi-agent system
│   ├── __init__.py
│   ├── base_agent.py                 # Base class for all agents
│   ├── coordinator_agent.py          # Coordinator agent
│   ├── research_agent.py             # Research agent
│   ├── code_generation_agent.py      # Code generation agent
│   ├── data_analysis_agent.py        # Data analysis agent
│   ├── state_manager.py              # State management
│   └── registry.py                   # Agent registry and factory
├── config/                           # Configuration system
│   ├── __init__.py
│   └── agent_config.py               # Agent configuration
└── utils/                            # Utility modules
    ├── gcs.py
    ├── tracing.py
    └── typing.py
```

## Extending the System

### Adding a New Specialized Agent

1. Create a new agent class inheriting from `BaseSpecializedAgent`:

```python
from app.agents.base_agent import BaseSpecializedAgent

class CustomAgent(BaseSpecializedAgent):
    def get_system_instruction(self) -> str:
        return "Your custom instructions..."

    def get_tools(self) -> list:
        def custom_tool(param: str) -> str:
            return f"Result for {param}"

        return [custom_tool]
```

2. Register in `AgentRegistry._AGENT_CLASSES`:

```python
_AGENT_CLASSES = {
    # ... existing agents
    "custom": CustomAgent,
}
```

3. Add description to `_AGENT_DESCRIPTIONS`

4. Update the registry's `create_multi_agent_system()` method

## Best Practices

1. **Use the Coordinator**: For complex tasks requiring multiple agents
2. **State Management**: Use state manager for inter-agent communication
3. **Configuration**: Externalize agent behavior through config
4. **Error Handling**: Agents should handle errors gracefully
5. **Testing**: Test agents individually and as a system
6. **Monitoring**: Use logging and tracing for observability

## Future Enhancements

- Real web search integration (Google Search API)
- Real code execution and validation
- Actual data processing with pandas/numpy
- Agent learning and improvement
- Dynamic agent creation based on needs
- Advanced coordination strategies (bidding, voting)
- Agent performance metrics and optimization

## Code Quality

The implementation follows project standards:
- Ruff linting compliance (line-length: 88)
- MyPy type checking
- Comprehensive docstrings
- Type hints throughout
- Thread-safe state management
- Factory and registry patterns

# Quick Start Guide: Multi-Agent System

## 5-Minute Quick Start

### Option 1: Use the Existing Root Agent (Backward Compatible)

```python
from app.agent import root_agent

# The root_agent now has multi-agent capabilities!
response = root_agent.query("What's the weather in San Francisco?")
```

### Option 2: Use the Coordinator Agent

```python
from app.agent import get_coordinator

# Get the coordinator
coordinator = get_coordinator()

# Orchestrate a task
result = coordinator.orchestrate(
    user_query="Research Python best practices and generate example code",
    context={"language": "python"}
)
print(result)
```

### Option 3: Use Specialized Agents Directly

```python
from app.agent import get_specialized_agent

# Get the research agent
research_agent = get_specialized_agent("research_agent")

# Create the ADK agent
adk_agent = research_agent.create_agent()

# Get tools
tools = research_agent.get_tools()

# Use a tool (e.g., web search)
web_search = tools[0]
results = web_search("machine learning frameworks", 5)
print(results)
```

## Available Agents

| Agent Name | Purpose | Key Capabilities |
|------------|---------|------------------|
| `coordinator` | Task orchestration | Delegates tasks, monitors status, synthesizes results |
| `research_agent` | Information gathering | Web search, research synthesis, fact verification |
| `code_generation_agent` | Code writing | Generate, review, refactor, test code in 5+ languages |
| `data_analysis_agent` | Data processing | Analyze datasets, stats, patterns, visualizations |

## Common Use Cases

### Use Case 1: Research a Topic

```python
from app.agent import get_specialized_agent

research = get_specialized_agent("research_agent")
tools = research.get_tools()

# Web search
search_tool = tools[0]
results = search_tool("AI trends 2025", 5)

# Synthesize research
synthesize_tool = tools[3]
summary = synthesize_tool(
    "AI trends 2025",
    "LLMs, multimodal AI, agent systems"
)
```

### Use Case 2: Generate Code

```python
from app.agent import get_specialized_agent

code_gen = get_specialized_agent("code_generation_agent")
tools = code_gen.get_tools()

# Generate code
generate_tool = tools[0]
code = generate_tool(
    "python",
    "Function to validate email addresses",
    "Use regex, include error handling"
)

# Review code
review_tool = tools[1]
review = review_tool(code, "python", "security,performance")
```

### Use Case 3: Analyze Data

```python
from app.agent import get_specialized_agent

data_agent = get_specialized_agent("data_analysis_agent")
tools = data_agent.get_tools()

# Analyze dataset
analyze_tool = tools[0]
analysis = analyze_tool(
    "Sales data Q4 2024",
    "trend",
    "revenue,quantity,region"
)

# Generate visualization
viz_tool = tools[3]
viz_spec = viz_tool("Sales data", "line", "Q4 2024 Sales Trends")
```

### Use Case 4: Coordinate Multiple Agents

```python
from app.agent import get_coordinator

coordinator = get_coordinator()
tools = coordinator.get_tools()

# Delegate to research agent
delegate = tools[0]
delegate(
    "research_agent",
    "Research Python web frameworks",
    "Focus on FastAPI and Django"
)

# Delegate to code generation agent
delegate(
    "code_generation_agent",
    "Generate a FastAPI hello world example",
    "Include error handling and type hints"
)

# Check status
status_tool = tools[3]
all_status = status_tool()
print(all_status)

# Get results
results_tool = tools[2]
research_results = results_tool("research_agent")
code_results = results_tool("code_generation_agent")
```

## Configuration

### Using Default Configuration

```python
from app.agent import root_agent

# Uses default configuration automatically
```

### Custom Configuration

```python
from app.config.agent_config import AgentConfig, set_agent_config

# Create custom config
config = AgentConfig(
    max_iterations=20,
    timeout_seconds=600,
    research_enable_web_search=True,
    code_gen_supported_languages=["python", "go", "rust"]
)

# Set as global config
set_agent_config(config)
```

### Environment Variables

```bash
# Set in your shell or .env file
export AGENT_DEFAULT_MODEL=gemini-2.0-flash
export AGENT_MAX_ITERATIONS=20
export RESEARCH_ENABLE_WEB_SEARCH=true
export CODE_GEN_ENABLE_VALIDATION=true
```

## Running Examples

```bash
# Run all examples
python examples_multi_agent.py

# Or import and run specific examples
python -c "from examples_multi_agent import example_1_basic_usage; example_1_basic_usage()"
```

## Accessing Agent Tools

Every specialized agent has tools. Here's how to access them:

```python
from app.agent import get_specialized_agent

# Get agent
agent = get_specialized_agent("research_agent")

# Get tools
tools = agent.get_tools()

# Tools are functions you can call directly
for i, tool in enumerate(tools):
    print(f"Tool {i}: {tool.__name__}")
    print(f"  Description: {tool.__doc__}")
```

## State Management

```python
from app.agent import get_agent_registry_instance

# Get the state manager
registry = get_agent_registry_instance()
state_manager = registry.state_manager

# Set global context
state_manager.set_global_context("project", "My Project")
state_manager.set_global_context("version", "1.0")

# Get global context
project = state_manager.get_global_context("project")

# Check agent states
all_states = state_manager.get_all_agent_states()
for name, state in all_states.items():
    print(f"{name}: {state.status} - {state.current_task}")
```

## Integration with Existing Code

### In AgentEngineApp

```python
from app.agent_engine_app import AgentEngineApp
from app.agent import root_agent

# Works seamlessly - root_agent now has multi-agent capabilities
agent_engine = AgentEngineApp(agent=root_agent)
```

### In Notebooks

```python
# In Jupyter notebooks
from app.agent import (
    root_agent,
    get_coordinator,
    get_specialized_agent,
    get_all_agents
)

# Use any of the patterns shown above
```

## Agent Tool Reference

### Coordinator Tools (5)

1. `delegate_task(agent_name, task, context)` - Delegate work
2. `get_agent_status(agent_name)` - Check status
3. `get_agent_results(agent_name)` - Get results
4. `get_all_agents_status()` - System status
5. `synthesize_results(agent_names, synthesis_prompt)` - Combine results

### Research Agent Tools (5)

1. `web_search(query, num_results)` - Search web
2. `gather_information(topic, sources)` - Gather info
3. `verify_information(claim, sources)` - Verify facts
4. `synthesize_research(topic, key_points)` - Create summary
5. `get_current_knowledge(topic)` - Access knowledge base

### Code Generation Agent Tools (5)

1. `generate_code(language, description, requirements)` - Generate code
2. `review_code(code, language, focus_areas)` - Review code
3. `generate_tests(code, language, test_framework)` - Generate tests
4. `refactor_code(code, language, goals)` - Refactor code
5. `explain_code(code, language, detail_level)` - Explain code

### Data Analysis Agent Tools (6)

1. `analyze_dataset(data_description, analysis_type, columns)` - Analyze data
2. `perform_statistical_analysis(data_description, tests, confidence_level)` - Stats
3. `identify_patterns(data_description, pattern_type)` - Find patterns
4. `generate_visualization(data_description, viz_type, title)` - Create viz
5. `clean_data(data_description, cleaning_operations)` - Clean data
6. `generate_report(analysis_summary, include_sections)` - Generate report

## Troubleshooting

### Issue: Agent not found

```python
from app.agent import get_all_agents

# Check available agents
agents = get_all_agents()
print(agents.keys())
# Output: dict_keys(['coordinator', 'research_agent', 'code_generation_agent', 'data_analysis_agent'])
```

### Issue: Understanding agent state

```python
from app.agent import get_specialized_agent

agent = get_specialized_agent("research_agent")
state = agent.get_agent_state()

print(f"Status: {state.status}")
print(f"Current task: {state.current_task}")
print(f"Results: {len(state.results)}")
```

### Issue: Resetting the system

```python
from app.agents.registry import reset_agent_registry

# Reset everything
reset_agent_registry()

# Re-import to get fresh system
from app.agent import root_agent, get_coordinator
```

## Next Steps

1. Read the full architecture documentation: `MULTI_AGENT_ARCHITECTURE.md`
2. Review the implementation summary: `IMPLEMENTATION_SUMMARY.md`
3. Run the examples: `python examples_multi_agent.py`
4. Experiment with the agents in a Jupyter notebook
5. Deploy to Vertex AI: `make backend`

## Getting Help

- Check the documentation in `MULTI_AGENT_ARCHITECTURE.md`
- Review examples in `examples_multi_agent.py`
- Look at the implementation in `app/agents/`
- Check configuration options in `app/config/agent_config.py`

## Key Takeaways

1. **Backward Compatible**: Existing code still works
2. **Easy to Use**: Simple API for common cases
3. **Powerful**: Complex multi-agent orchestration available
4. **Configurable**: Customize behavior via configuration
5. **Extensible**: Easy to add new agents and tools
6. **Production Ready**: Thread-safe, typed, documented

Start simple and progressively use more advanced features as needed!

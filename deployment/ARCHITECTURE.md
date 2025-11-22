# Multi-Agent System Architecture

## Overview

This document provides a detailed architecture overview of the multi-agent AI system deployed on Google Cloud Platform.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External Clients                                   │
│                    (Web, Mobile, API Consumers)                             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Cloud Load Balancer                                   │
│                     (Global HTTP(S) Load Balancer)                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Multi-Agent Orchestrator                                │
│                         (Cloud Run Service)                                  │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │   Request      │  │     Agent      │  │    Response    │                │
│  │   Router       │→ │  Coordinator   │→ │   Aggregator   │                │
│  │                │  │                │  │                │                │
│  │ • Parse input  │  │ • Select agents│  │ • Combine      │                │
│  │ • Validate     │  │ • Orchestrate  │  │   results      │                │
│  │ • Prioritize   │  │ • Monitor      │  │ • Format       │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
└──────────┬───────────────────┬───────────────────┬──────────────────────────┘
           │                   │                   │
           │                   │                   │
           ▼                   ▼                   ▼
    ┌────────────┐      ┌────────────┐     ┌────────────┐
    │  Research  │      │    Code    │     │  Analysis  │
    │   Agent    │      │   Agent    │     │   Agent    │
    │            │      │            │     │            │
    │ Vertex AI  │      │ Vertex AI  │     │ Vertex AI  │
    │ Agent      │      │ Agent      │     │ Agent      │
    │ Engine     │      │ Engine     │     │ Engine     │
    └────┬───────┘      └────┬───────┘     └────┬───────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
  ┌──────────────┐                      ┌──────────────┐
  │   Pub/Sub    │                      │  Firestore   │
  │              │                      │              │
  │ • Task Queue │                      │ • Agent State│
  │ • Results    │                      │ • Sessions   │
  │ • DLQ        │                      │ • Cache      │
  └──────┬───────┘                      └──────┬───────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   Monitoring & Analytics     │
         │                              │
         │ • Cloud Trace                │
         │ • Cloud Logging              │
         │ • Cloud Monitoring           │
         │ • BigQuery                   │
         └──────────────────────────────┘
```

## Component Details

### 1. Multi-Agent Orchestrator (Cloud Run)

**Purpose:** Central coordination hub for all agent interactions

**Key Responsibilities:**
- Receive and validate incoming requests
- Analyze requests to determine required agents
- Route tasks to appropriate specialist agents
- Manage agent-to-agent handoffs
- Aggregate results from multiple agents
- Handle errors and retries
- Track request lifecycle

**Technology Stack:**
- Runtime: Python 3.11
- Framework: Google ADK
- Hosting: Cloud Run (fully managed, auto-scaling)
- Concurrency: Async/await pattern

**Scaling Configuration:**
- Min instances: 1 (staging), 2 (prod)
- Max instances: 5 (staging), 10 (prod)
- CPU: 2 vCPU
- Memory: 4 GiB
- Request timeout: 60 minutes
- Concurrency: 80 requests per instance

### 2. Specialist Agents (Vertex AI Agent Engine)

#### Research Agent
**Purpose:** Information gathering, web search, document analysis

**Capabilities:**
- Web search integration
- Document parsing
- Citation tracking
- Knowledge synthesis

**Model:** Gemini 2.0 Flash
**Max Concurrent Tasks:** 3-10 (depending on environment)
**Timeout:** 3 minutes

#### Code Agent
**Purpose:** Code generation, review, and analysis

**Capabilities:**
- Code generation (Python, JavaScript, Java, Go)
- Code review and suggestions
- Vulnerability scanning
- Documentation generation

**Model:** Gemini 2.0 Flash
**Max Concurrent Tasks:** 2-8 (depending on environment)
**Timeout:** 4 minutes

#### Analysis Agent
**Purpose:** Data analysis and insights

**Capabilities:**
- Statistical analysis
- Data visualization
- Trend detection
- Report generation

**Model:** Gemini 2.0 Flash
**Max Concurrent Tasks:** 2-8 (depending on environment)
**Timeout:** 3 minutes

### 3. Communication Layer (Pub/Sub)

**Topics:**
1. `my-agent-agent-tasks` - Incoming tasks for agents
2. `my-agent-agent-results` - Agent execution results
3. `my-agent-agent-dlq` - Dead letter queue for failed tasks

**Subscriptions:**
- Task subscription: 10-minute ack deadline, retry policy
- Result subscription: 5-minute ack deadline
- DLQ retention: 7 days

**Message Flow:**
```
Orchestrator → Task Topic → Task Subscription → Agent
Agent → Result Topic → Result Subscription → Orchestrator
Failed Messages → DLQ Topic (after 5 attempts)
```

### 4. State Management (Firestore)

**Database:** Firestore Native Mode

**Collections:**
- `agent_sessions` - Active agent sessions
- `agent_state` - Agent execution state
- `task_cache` - Cached results for common tasks
- `handoff_logs` - Agent-to-agent handoff records

**Concurrency:** Optimistic locking
**Backups:** Automated daily backups (prod only)

### 5. Storage (Cloud Storage)

**Buckets:**
1. `{project}-my-agent-agent-configs`
   - Agent configurations
   - Feature flags
   - Deployment markers

2. `{project}-my-agent-logs-data`
   - Build logs
   - Application logs
   - Audit logs

3. `{project}-my-agent-load-test`
   - Load test results
   - Performance benchmarks

**Access Control:** Uniform bucket-level access
**Versioning:** Enabled on config bucket
**Lifecycle:** 30-day retention on log bucket

### 6. Analytics & Storage (BigQuery)

**Datasets:**

1. **my_agent_telemetry**
   - Distributed traces
   - Performance metrics
   - System logs
   - Partitioned by day

2. **my_agent_feedback**
   - User feedback
   - Ratings
   - Feature requests
   - Partitioned by day

3. **my_agent_agent_metrics**
   - Agent performance data
   - Handoff statistics
   - Token usage
   - Error rates
   - Partitioned by day

**Retention:**
- Telemetry: 90 days
- Feedback: 365 days
- Metrics: 365 days

## Data Flow

### Standard Request Flow

```
1. Client Request
   └→ Load Balancer
      └→ Orchestrator (Cloud Run)
         └→ Request Router
            ├→ Validate input
            ├→ Check cache (Firestore)
            └→ Determine required agents

2. Task Distribution
   └→ Orchestrator
      └→ Publish to Task Topic (Pub/Sub)
         └→ Task Subscription
            └→ Specialist Agent(s) (Vertex AI)

3. Agent Execution
   └→ Agent receives task
      ├→ Update state (Firestore)
      ├→ Execute task
      ├→ Log metrics (Cloud Logging)
      └→ Publish result (Pub/Sub)

4. Result Aggregation
   └→ Orchestrator
      └→ Receive from Result Subscription
         ├→ Aggregate results
         ├→ Cache result (Firestore)
         └→ Format response

5. Response Delivery
   └→ Return to client
      ├→ Log telemetry (Cloud Trace)
      └→ Store metrics (BigQuery)
```

### Agent Handoff Flow

```
1. Primary Agent Processing
   └→ Research Agent analyzing request
      └→ Determines code generation needed
         └→ Initiates handoff

2. Handoff Execution
   └→ Research Agent
      ├→ Saves intermediate state (Firestore)
      ├→ Creates handoff task
      └→ Publishes to Task Topic
         └→ Code Agent receives task

3. Specialist Processing
   └→ Code Agent
      ├→ Loads context from Firestore
      ├→ Executes specialized task
      ├→ Saves results
      └→ May handoff to another agent or return to orchestrator

4. Result Consolidation
   └→ Orchestrator
      └→ Receives all agent results
         └→ Consolidates into final response
```

## Security Architecture

### Identity & Access Management

**Service Accounts:**
1. `my-agent-cb@{cicd-project}.iam` - CI/CD runner
2. `my-agent-multi-agent@{project}.iam` - Multi-agent system
3. Vertex AI service agents (auto-created)

**IAM Roles:**
- Multi-agent SA: aiplatform.user, pubsub.publisher, datastore.user, secretmanager.secretAccessor
- CI/CD SA: cloudbuild.builds.builder, storage.admin, iam.serviceAccountUser

### Network Security

- **VPC:** Default VPC (can be customized for private networking)
- **Firewall:** Cloud Run ingress control
- **TLS:** All communication encrypted in transit
- **API Keys:** Stored in Secret Manager

### Data Security

- **Encryption at Rest:** All GCS, Firestore, BigQuery data
- **Encryption in Transit:** TLS 1.3 for all connections
- **PII Detection:** Configurable via feature flags
- **Content Filtering:** Enabled by default

## Monitoring & Observability

### Tracing (Cloud Trace)

**Instrumentation Points:**
- HTTP requests (auto)
- Agent handoffs (custom)
- Agent executions (custom)
- Pub/Sub operations (custom)
- Firestore operations (custom)

**Sampling Rates:**
- Dev: 100%
- Staging: 50%
- Prod: 10%

### Logging (Cloud Logging)

**Log Types:**
- Application logs (structured JSON)
- Agent telemetry logs
- Feedback logs
- Audit logs

**Log Sinks:**
- Telemetry → BigQuery
- Feedback → BigQuery
- Agent metrics → BigQuery

### Metrics (Cloud Monitoring)

**System Metrics:**
- Request rate, latency, errors
- Instance count, CPU, memory
- Pub/Sub queue depth
- Firestore operations

**Custom Metrics:**
- Agent handoff latency
- Agent queue depth
- Token usage per agent
- Handoff success rate

## Disaster Recovery

### Backup Strategy

**Firestore:**
- Automated daily backups (prod)
- Point-in-time recovery available
- 30-day backup retention

**Configuration:**
- Versioned in GCS
- Deployment markers for rollback
- Git version control

**BigQuery:**
- Automatic table snapshots
- 7-day time travel
- Cross-region replication (optional)

### Recovery Procedures

1. **Agent Failure:** Auto-restart via Cloud Run
2. **Complete Outage:** Restore from latest backup
3. **Bad Deployment:** Rollback to previous version via deployment markers
4. **Data Loss:** Restore from BigQuery time travel or Firestore backups

## Scalability

### Horizontal Scaling

- **Cloud Run:** Auto-scales based on CPU/requests
- **Vertex AI Agents:** Scale via max concurrent tasks
- **Pub/Sub:** Automatically scales, virtually unlimited
- **Firestore:** Automatically scales, 1M operations/second

### Vertical Scaling

- **Cloud Run:** CPU and memory configurable per service
- **BigQuery:** Query slots auto-allocated
- **Firestore:** No manual intervention needed

### Performance Optimization

- **Caching:** Firestore cache for frequent queries
- **Batching:** Request batching for efficiency
- **Deduplication:** Eliminate redundant concurrent requests
- **Connection Pooling:** Reuse connections to backend services

## Cost Optimization

### Cost Drivers

1. **Vertex AI Agent Engine:** Token consumption
2. **Cloud Run:** vCPU-seconds and memory
3. **Pub/Sub:** Message throughput
4. **Firestore:** Read/write operations
5. **BigQuery:** Storage and query costs

### Optimization Strategies

- **Right-sizing:** Adjust instance sizes based on actual usage
- **Auto-scaling:** Minimize idle instances
- **Caching:** Reduce redundant AI calls
- **Batch Processing:** Group operations where possible
- **Data Lifecycle:** Archive old data to cheaper storage
- **Sampling:** Reduce trace sampling in production

## Future Enhancements

### Planned Features

- Multi-region deployment for high availability
- Agent learning from user feedback
- Advanced collaboration between agents
- Multimodal capabilities (image, video)
- Predictive task assignment using ML

### Technical Debt

- Implement comprehensive integration tests
- Add performance benchmarking suite
- Create automated capacity planning
- Enhance error recovery mechanisms

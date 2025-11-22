# Multi-Agent System - Complete Deployment Guide

## Configuration Management

### Environment-Specific Configurations

The multi-agent system uses environment-specific configurations stored in `deployment/config/`:

#### Directory Structure
```
deployment/config/
├── dev/
│   └── agent_config.yaml          # Development environment settings
├── staging/
│   └── agent_config.yaml          # Staging environment settings
├── prod/
│   └── agent_config.yaml          # Production environment settings
├── feature_flags.yaml             # Feature flags across environments
└── secrets_template.yaml          # Template for Secret Manager
```

### Configuration Files

#### 1. Agent Configuration (`agent_config.yaml`)

Each environment has its own agent configuration with:
- **Agent Settings**: Model selection, timeout, retries
- **Resource Limits**: CPU, memory, instance counts
- **Queue Configuration**: Message limits, retention periods
- **Feature Flags**: Environment-specific feature toggles
- **Monitoring**: Trace sampling rates, log levels
- **Rate Limits**: Requests/minute, concurrent requests

Example structure:
```yaml
environment: staging
agents:
  orchestrator:
    enabled: true
    model: gemini-2.0-flash
    max_retries: 3
    timeout_seconds: 300
  specialist_agents:
    - name: research_agent
      type: research
      max_concurrent_tasks: 5
resources:
  orchestrator:
    min_instances: 1
    max_instances: 5
```

#### 2. Feature Flags (`feature_flags.yaml`)

Centralized feature flag management for:
- Multi-agent capabilities (handoff, parallel execution, prioritization)
- Agent-specific features (web search, code generation, analysis)
- Performance optimizations (caching, batching, deduplication)
- Observability features (tracing, profiling, cost tracking)
- Safety features (content filtering, PII detection, rate limiting)
- Experimental features (multimodal, learning, collaboration)

### Configuration Deployment

Configurations are automatically deployed during CI/CD:

**Staging:**
```bash
gsutil cp deployment/config/staging/agent_config.yaml \
  gs://${STAGING_PROJECT_ID}-my-agent-agent-configs/
```

**Production:**
```bash
gsutil cp deployment/config/prod/agent_config.yaml \
  gs://${PROD_PROJECT_ID}-my-agent-agent-configs/
```

### Secrets Management

#### Setting Up Secrets

1. **Create secrets in Secret Manager:**
```bash
# API Keys
echo -n "your-api-key" | gcloud secrets create my-agent-agent-api-keys \
  --data-file=- \
  --replication-policy="automatic" \
  --project=${PROJECT_ID}
```

2. **Grant service account access:**
```bash
gcloud secrets add-iam-policy-binding my-agent-agent-api-keys \
  --member="serviceAccount:my-agent-multi-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=${PROJECT_ID}
```

3. **Access secrets from code:**
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/my-agent-agent-api-keys/versions/latest"
response = client.access_secret_version(request={"name": name})
secret_value = response.payload.data.decode("UTF-8")
```

## Monitoring & Observability

### 1. Cloud Trace - Distributed Tracing

#### Trace Configuration
- Located in `deployment/monitoring/tracing_config.yaml`
- Environment-specific sampling rates
- Custom span instrumentation for:
  - Agent orchestration
  - Agent handoffs
  - Tool/function calls
  - Pub/Sub operations
  - Firestore operations

#### Key Spans to Monitor
- `agent.orchestrator.request` - Full request lifecycle
- `agent.handoff` - Agent-to-agent transitions
- `agent.execution` - Individual agent tasks
- `agent.tool_call` - External tool invocations

### 2. Cloud Monitoring - Dashboards & Alerts

#### Dashboard Setup
Deploy the pre-configured dashboard:
```bash
gcloud monitoring dashboards create --config-from-file=deployment/monitoring/dashboard_config.json
```

#### Key Metrics
- **Request Rate**: Requests per second by agent type
- **Response Latency**: P50, P95, P99 latencies
- **Error Rate**: 5xx errors per minute
- **Instance Count**: Auto-scaling behavior
- **Queue Depth**: Pending tasks in Pub/Sub
- **Handoff Latency**: Agent-to-agent transition time
- **Token Usage**: Cost tracking per agent

#### Alerting Policies

Deploy alerting policies from `deployment/monitoring/alerting_policies.yaml`:

**Critical Alerts:**
- High error rate (>10 errors/min)
- Service unavailable (no successful requests in 5 min)

**Warning Alerts:**
- High latency (P95 > 5 seconds)
- Queue backup (>1000 undelivered messages)
- High handoff failure rate (>5 failures/min)

**Info Alerts:**
- High token usage (>1M tokens/hour)
- Auto-scaling events

### 3. BigQuery Analytics

#### Datasets Created by Terraform
- `my_agent_telemetry` - Trace and log data
- `my_agent_feedback` - User feedback
- `my_agent_agent_metrics` - Multi-agent performance metrics

#### Key Tables
- `agent_performance` - Agent execution metrics
  - Partitioned by timestamp
  - Includes: duration, status, tokens_used, handoff_count

#### Sample Queries

**Average agent execution time:**
```sql
SELECT
  agent_type,
  AVG(duration_ms) as avg_duration_ms,
  COUNT(*) as total_executions
FROM `${PROJECT_ID}.my_agent_agent_metrics.agent_performance`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY agent_type
ORDER BY avg_duration_ms DESC
```

**Agent handoff patterns:**
```sql
SELECT
  agent_type,
  status,
  COUNT(*) as count,
  AVG(handoff_count) as avg_handoffs
FROM `${PROJECT_ID}.my_agent_agent_metrics.agent_performance`
WHERE handoff_count > 0
GROUP BY agent_type, status
```

## Resource Requirements

### Minimum Requirements (Development)

| Resource | Specification |
|----------|--------------|
| **Cloud Run** | 1-3 instances, 1 vCPU, 2Gi memory |
| **Vertex AI** | 3 agent instances (1 per specialist) |
| **Pub/Sub** | 3 topics, 3 subscriptions |
| **Firestore** | 1 database, NATIVE mode |
| **GCS** | 3 buckets (configs, logs, load tests) |
| **BigQuery** | 3 datasets, ~10GB storage |

**Estimated Monthly Cost (Dev):** $50-$150

### Recommended Requirements (Staging)

| Resource | Specification |
|----------|--------------|
| **Cloud Run** | 1-5 instances, 2 vCPU, 4Gi memory |
| **Vertex AI** | 5 agent instances |
| **Pub/Sub** | 3 topics, 3 subscriptions (5000 msg capacity) |
| **Firestore** | 1 database with backups |
| **GCS** | 3 buckets with versioning |
| **BigQuery** | 3 datasets, ~100GB storage |

**Estimated Monthly Cost (Staging):** $200-$500

### Production Requirements

| Resource | Specification |
|----------|--------------|
| **Cloud Run** | 2-10 instances, 2 vCPU, 4Gi memory |
| **Vertex AI** | 10+ agent instances |
| **Pub/Sub** | 3 topics, 3 subscriptions (10000 msg capacity) |
| **Firestore** | Multi-region, automated backups |
| **GCS** | 3 buckets, multi-region, versioning |
| **BigQuery** | 3 datasets, ~1TB storage |
| **Monitoring** | Custom dashboards, alerting channels |

**Estimated Monthly Cost (Production):** $500-$2000+

*Costs vary significantly based on usage (token consumption, request volume, etc.)*

### API Quotas

Ensure sufficient quotas for:
- **Vertex AI API**: Agent Engine requests
- **Cloud Run**: Concurrent requests
- **Pub/Sub**: Messages per second
- **Firestore**: Read/write operations per second
- **BigQuery**: Query slots

### Request Quota Increases

```bash
gcloud services enable serviceconsumermanagement.googleapis.com
# Contact Google Cloud support for quota increases
```

## Deployment Checklist

### Pre-Deployment

- [ ] **Projects Created**
  - [ ] CICD project configured
  - [ ] Staging project configured
  - [ ] Production project configured

- [ ] **Repository Setup**
  - [ ] Git repository created
  - [ ] Repository connected to Cloud Build
  - [ ] Branch protection rules configured

- [ ] **Terraform Variables**
  - [ ] `deployment/terraform/vars/env.tfvars` updated
  - [ ] Project IDs configured
  - [ ] Region selected
  - [ ] Host connection name set
  - [ ] Repository name set

- [ ] **Agent Configurations**
  - [ ] `deployment/config/dev/agent_config.yaml` reviewed
  - [ ] `deployment/config/staging/agent_config.yaml` reviewed
  - [ ] `deployment/config/prod/agent_config.yaml` reviewed
  - [ ] Feature flags configured

- [ ] **Secrets Management**
  - [ ] API keys identified
  - [ ] Secrets created in Secret Manager
  - [ ] IAM permissions granted

### Infrastructure Deployment

- [ ] **Enable Required APIs**
  ```bash
  gcloud services enable serviceusage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com
  ```

- [ ] **Terraform Deployment**
  - [ ] `terraform init` executed
  - [ ] `terraform plan` reviewed
  - [ ] `terraform apply` completed successfully
  - [ ] All resources created without errors

- [ ] **Verify Infrastructure**
  - [ ] Service accounts created
  - [ ] IAM roles assigned
  - [ ] GCS buckets created
  - [ ] Pub/Sub topics and subscriptions created
  - [ ] Firestore database created
  - [ ] BigQuery datasets created

### Application Deployment

- [ ] **Development Testing**
  - [ ] Unit tests passing
  - [ ] Integration tests passing
  - [ ] Multi-agent tests passing
  - [ ] Configuration validation passing

- [ ] **Staging Deployment**
  - [ ] Agent configurations deployed to GCS
  - [ ] Agents deployed to Vertex AI
  - [ ] Deployment health verified
  - [ ] Load tests executed successfully

- [ ] **Production Deployment**
  - [ ] Staging tests passed
  - [ ] Production configurations deployed
  - [ ] Manual approval obtained
  - [ ] Production agents deployed
  - [ ] Deployment markers created

### Post-Deployment

- [ ] **Monitoring Setup**
  - [ ] Cloud Monitoring dashboard deployed
  - [ ] Alerting policies configured
  - [ ] Notification channels set up
  - [ ] SLOs defined

- [ ] **Observability Verification**
  - [ ] Traces visible in Cloud Trace
  - [ ] Logs flowing to Cloud Logging
  - [ ] Metrics appearing in Cloud Monitoring
  - [ ] BigQuery tables receiving data

- [ ] **Testing**
  - [ ] End-to-end test successful
  - [ ] Multi-agent handoff working
  - [ ] Error handling verified
  - [ ] Performance acceptable

- [ ] **Documentation**
  - [ ] Runbook created/updated
  - [ ] On-call procedures documented
  - [ ] Rollback procedure documented

## Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails

**Symptom:** Terraform returns errors during `apply`

**Solutions:**
- Check API enablement: `gcloud services list --enabled`
- Verify IAM permissions for Terraform service account
- Check resource quotas in Cloud Console
- Review Terraform logs for specific errors

#### 2. Agent Deployment Fails

**Symptom:** Agent Engine deployment returns errors

**Solutions:**
- Verify service account has `roles/aiplatform.user`
- Check GCS bucket exists and is accessible
- Ensure requirements.txt is properly formatted
- Review Cloud Build logs for details

#### 3. High Latency

**Symptom:** Agent responses are slow

**Investigations:**
- Check Cloud Monitoring dashboard for bottlenecks
- Review Cloud Trace for slow operations
- Check Pub/Sub queue depth
- Verify agent instance count (may need scaling)
- Check external API latencies

#### 4. Agent Handoff Failures

**Symptom:** Tasks fail during agent transitions

**Solutions:**
- Verify all specialist agents are deployed and running
- Check Pub/Sub topics and subscriptions are healthy
- Review Firestore for state consistency
- Check agent logs for handoff errors
- Verify IAM permissions for Pub/Sub

#### 5. Missing Traces/Logs

**Symptom:** Data not appearing in Cloud Trace or Logging

**Solutions:**
- Verify Cloud Trace API is enabled
- Check service account has `roles/cloudtrace.agent`
- Review tracing configuration sampling rates
- Ensure OpenTelemetry is properly initialized
- Check log sink filters are correct

#### 6. Configuration Not Loading

**Symptom:** Agents using default configuration

**Solutions:**
- Verify GCS bucket contains config files
- Check service account has `roles/storage.objectViewer`
- Ensure CONFIG_BUCKET environment variable is set
- Review application logs for config loading errors

### Getting Help

1. **Check Documentation**
   - Review this deployment guide
   - Check [ADK Documentation](https://google.github.io/adk-docs/)
   - Review [Google Cloud Documentation](https://cloud.google.com/docs)

2. **Review Logs**
   - Cloud Logging: Application and system logs
   - Cloud Build: Deployment logs
   - Cloud Trace: Request traces

3. **Contact Support**
   - Google Cloud Support (if you have a support plan)
   - GitHub Issues for ADK or Agent Starter Pack
   - Internal team Slack/communication channels

### Emergency Procedures

#### Rollback to Previous Version

1. Identify last known good deployment:
```bash
gsutil ls gs://${PROJECT_ID}-my-agent-agent-configs/deployments/
```

2. Find the commit SHA of the working version

3. Deploy previous version:
```bash
git checkout <previous-commit-sha>
# Trigger deployment pipeline or manual deploy
```

#### Disable Multi-Agent Features

If multi-agent features are causing issues, you can disable them via feature flags:

1. Edit `deployment/config/prod/agent_config.yaml`
2. Set problematic features to `false`
3. Deploy configuration:
```bash
gsutil cp deployment/config/prod/agent_config.yaml \
  gs://${PROJECT_ID}-my-agent-agent-configs/agent_config.yaml
```
4. Restart agents to pick up new configuration

#### Emergency Scaling

If system is overloaded:

```bash
# Manually scale Cloud Run
gcloud run services update my-agent-orchestrator \
  --min-instances=5 \
  --max-instances=20 \
  --region=us-central1 \
  --project=${PROJECT_ID}
```

# Multi-Agent System Deployment Guide

This folder contains the infrastructure-as-code and CI/CD pipeline configurations for deploying a **Multi-Agent AI System** on Google Cloud Platform.

The multi-agent system uses:
- [**Terraform**](http://terraform.io) for infrastructure provisioning
- [**Cloud Build**](https://cloud.google.com/build/) for CI/CD orchestration
- [**Cloud Run**](https://cloud.google.com/run) for serverless agent execution
- [**Pub/Sub**](https://cloud.google.com/pubsub) for agent communication
- [**Firestore**](https://cloud.google.com/firestore) for agent state management
- [**Vertex AI Agent Engine**](https://cloud.google.com/vertex-ai) for agent hosting

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Multi-Agent System Components](#multi-agent-system-components)
3. [Deployment Workflow](#deployment-workflow)
4. [Prerequisites](#prerequisites)
5. [Setup Guide](#setup-guide)
6. [Configuration Management](#configuration-management)
7. [Monitoring & Observability](#monitoring--observability)
8. [Resource Requirements](#resource-requirements)
9. [Deployment Checklist](#deployment-checklist)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Multi-Agent System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                        │
│                    (Streamlit / API Gateway)                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Orchestrator                         │
│                      (Cloud Run Service)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Request      │  │ Agent        │  │ Response     │             │
│  │ Router       │→ │ Coordinator  │→ │ Aggregator   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │  Research    │ │    Code      │ │  Analysis    │
         │   Agent      │ │   Agent      │ │   Agent      │
         │ (Vertex AI)  │ │ (Vertex AI)  │ │ (Vertex AI)  │
         └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                │                │                │
                └────────────────┼────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
         ┌──────────────────┐      ┌──────────────────┐
         │   Pub/Sub         │      │   Firestore      │
         │ (Task Queue)      │      │ (State Store)    │
         └──────────────────┘      └──────────────────┘
                    │
                    ▼
         ┌──────────────────────────────────┐
         │  Monitoring & Observability      │
         │  - Cloud Trace                   │
         │  - Cloud Logging                 │
         │  - Cloud Monitoring              │
         │  - BigQuery (Analytics)          │
         └──────────────────────────────────┘
```

### Component Communication Flow

```
User Request
    ↓
Orchestrator receives request
    ↓
Orchestrator analyzes request and determines required agents
    ↓
Tasks published to Pub/Sub topics
    ↓
Specialist agents subscribe and process tasks
    ↓
Agents update Firestore with intermediate state
    ↓
Agents publish results to result topics
    ↓
Orchestrator aggregates results
    ↓
Response returned to user
    ↓
Metrics logged to BigQuery, traces to Cloud Trace
```

## Multi-Agent System Components

### 1. Multi-Agent Orchestrator
- **Purpose**: Coordinates multiple specialist agents
- **Technology**: Cloud Run (auto-scaling)
- **Capabilities**:
  - Request routing to appropriate agents
  - Parallel task execution
  - Result aggregation
  - Error handling and retries

### 2. Specialist Agents
- **Research Agent**: Information gathering and web search
- **Code Agent**: Code generation and review
- **Analysis Agent**: Data analysis and insights
- **Technology**: Vertex AI Agent Engine

### 3. Communication Layer
- **Pub/Sub Topics**: Agent task queues and result queues
- **Dead Letter Queue**: Failed task handling
- **Message Retention**: 24 hours for tasks, 7 days for DLQ

### 4. State Management
- **Firestore**: Stores agent state, session data, and intermediate results
- **Concurrency**: Optimistic concurrency control

### 5. Storage
- **GCS Buckets**:
  - Agent configurations
  - Load test results
  - Build logs
  - Deployment artifacts

### 6. Observability
- **Cloud Trace**: Distributed tracing for multi-agent flows
- **Cloud Logging**: Structured logging with trace correlation
- **Cloud Monitoring**: Custom metrics and dashboards
- **BigQuery**: Long-term analytics and performance tracking

## Deployment Workflow

![Deployment Workflow](https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/deployment_workflow.png)

**Description:**

1. CI Pipeline (`deployment/ci/pr_checks.yaml`):

   - Triggered on pull request creation/update
   - Runs unit, integration, and multi-agent specific tests
   - Validates agent configurations
   - Performs code quality checks

2. CD Pipeline (`deployment/cd/staging.yaml`):

   - Triggered on merge to `main` branch
   - Deploys agent configurations to GCS
   - Deploys agents to Vertex AI Agent Engine
   - Verifies deployment health
   - Performs load testing

3. Production Deployment (`deployment/cd/deploy-to-prod.yaml`):
   - Triggered after successful staging deployment
   - Requires manual approval
   - Deploys production agent configurations
   - Deploys to production environment
   - Creates deployment markers for rollback

## Configuration Management

The multi-agent system uses environment-specific configurations:

- **Agent Configurations**: `deployment/config/{env}/agent_config.yaml`
- **Feature Flags**: `deployment/config/feature_flags.yaml`
- **Secrets Template**: `deployment/config/secrets_template.yaml`

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#configuration-management) for detailed configuration instructions.

## Monitoring & Observability

### Dashboards
- **Dashboard Config**: `deployment/monitoring/dashboard_config.json`
- **Metrics**: Request rate, latency, errors, queue depth, handoff latency

### Alerting
- **Alerting Policies**: `deployment/monitoring/alerting_policies.yaml`
- **Critical**: High error rate, service unavailable
- **Warning**: High latency, queue backup, handoff failures
- **Info**: Token usage, scaling events

### Tracing
- **Configuration**: `deployment/monitoring/tracing_config.yaml`
- **Key Spans**: Orchestration, handoffs, agent execution, tool calls

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#monitoring--observability) for detailed monitoring setup.

## Resource Requirements

| Environment | Cloud Run | Vertex AI | Cost Estimate |
|------------|-----------|-----------|---------------|
| **Dev** | 1-3 instances, 1 vCPU, 2Gi | 3 agents | $50-$150/mo |
| **Staging** | 1-5 instances, 2 vCPU, 4Gi | 5 agents | $200-$500/mo |
| **Production** | 2-10 instances, 2 vCPU, 4Gi | 10+ agents | $500-$2000+/mo |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#resource-requirements) for complete resource specifications.

## Deployment Checklist

Use this checklist to ensure successful deployment:

- [ ] Projects created and configured
- [ ] Repository connected to Cloud Build
- [ ] Terraform variables configured
- [ ] Agent configurations reviewed
- [ ] Secrets created in Secret Manager
- [ ] Infrastructure deployed via Terraform
- [ ] Monitoring dashboards and alerts configured
- [ ] Application deployed and tested

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#deployment-checklist) for the complete checklist.

## Prerequisites

> **Quick Start:** For rapid development setup, see [QUICK_START.md](QUICK_START.md)
>
> **Complete Guide:** For production deployment, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
>
> **Architecture:** For system architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md)

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`agent-starter-pack setup-cicd` CLI command](https://github.com/GoogleCloudPlatform/agent-starter-pack/blob/main/docs/cli/setup_cicd.md). Currently only supporting Github.

**Prerequisites:**

1. A set of Google Cloud projects:
   - Staging project
   - Production project
   - CI/CD project (can be the same as staging or production)
2. Terraform installed on your local machine
3. Enable required APIs in the CI/CD project. This will be required for the Terraform deployment:

   ```bash
   gcloud config set project $YOUR_CI_CD_PROJECT_ID
   gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
   ```

## Step-by-Step Guide

1. **Create a Git Repository using your favorite Git provider (GitHub, GitLab, Bitbucket, etc.)**

2. **Connect Your Repository to Cloud Build**
   For detailed instructions, visit: [Cloud Build Repository Setup](https://cloud.google.com/build/docs/repositories#whats_next).<br>

   ![Alt text](https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/connection_cb.gif)

3. **Configure Terraform Variables**

   - Edit [`deployment/terraform/vars/env.tfvars`](../terraform/vars/env.tfvars) with your Google Cloud settings.

   | Variable               | Description                                                     | Required |
   | ---------------------- | --------------------------------------------------------------- | :------: |
   | project_name           | Project name used as a base for resource naming                 |   Yes    |
   | prod_project_id        | **Production** Google Cloud Project ID for resource deployment. |   Yes    |
   | staging_project_id     | **Staging** Google Cloud Project ID for resource deployment.    |   Yes    |
   | cicd_runner_project_id | Google Cloud Project ID where CI/CD pipelines will execute.     |   Yes    |
   | region                 | Google Cloud region for resource deployment.                    |   Yes    |
   | host_connection_name   | Name of the host connection you created in Cloud Build          |   Yes    |
   | repository_name        | Name of the repository you added to Cloud Build                 |   Yes    |

   Other optional variables may include: telemetry and feedback log filters, service account roles, and for projects requiring data ingestion: pipeline cron schedule, pipeline roles, and datastore-specific configurations.

4. **Deploy Infrastructure with Terraform**

   - Open a terminal and navigate to the Terraform directory:

   ```bash
   cd deployment/terraform
   ```

   - Initialize Terraform:

   ```bash
   terraform init
   ```

   - Apply the Terraform configuration:

   ```bash
   terraform apply --var-file vars/env.tfvars
   ```

   - Type 'yes' when prompted to confirm

After completing these steps, your infrastructure will be set up and ready for deployment!

## Dev Deployment

For End-to-end testing of the application, including tracing and feedback sinking to BigQuery, without the need to trigger a CI/CD pipeline.

First, enable required Google Cloud APIs:

```bash
gcloud config set project <your-dev-project-id>
gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com
```

After you edited the relative [`env.tfvars` file](../terraform/dev/vars/env.tfvars), follow the following instructions:

```bash
cd deployment/terraform/dev
terraform init
terraform apply --var-file vars/env.tfvars
```

Then deploy the application using the following command (from the root of the repository):

```bash
make backend
```

### End-to-end Demo video

<a href="https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/template_deployment_demo.mp4">
  <img src="https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/preview_video.png" alt="Watch the video" width="300"/>
</a>

## Troubleshooting

### Common Issues

- **Terraform Apply Fails**: Check API enablement and IAM permissions
- **Agent Deployment Fails**: Verify service account permissions and GCS bucket access
- **High Latency**: Check Cloud Monitoring dashboard and agent instance counts
- **Agent Handoff Failures**: Verify all specialist agents are running and Pub/Sub is healthy
- **Missing Traces/Logs**: Check Cloud Trace API and service account permissions

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for detailed troubleshooting steps.

## Documentation Index

- **[README.md](README.md)** - This file, overview and basic setup
- **[QUICK_START.md](QUICK_START.md)** - Fast setup for development (5 minutes) and production (30 minutes)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide with configuration, monitoring, and troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture, components, and data flows

## Multi-Agent System Features

### Agent Capabilities
- **Research Agent**: Web search, document analysis, citation tracking
- **Code Agent**: Code generation, review, vulnerability scanning
- **Analysis Agent**: Statistical analysis, data visualization, insights

### System Features
- **Agent Handoff**: Seamless task transfer between specialist agents
- **Parallel Execution**: Multiple agents working concurrently
- **Task Prioritization**: Intelligent task queue management
- **Auto-Scaling**: Dynamic resource allocation based on load
- **Distributed Tracing**: Full visibility into multi-agent workflows
- **Cost Tracking**: Per-agent and per-task cost monitoring

### Configuration Features
- **Environment-Specific Configs**: Separate settings for dev, staging, prod
- **Feature Flags**: Granular control over system capabilities
- **Secrets Management**: Secure API key storage in Secret Manager
- **Dynamic Configuration**: Update configs without redeployment

## Additional Resources

- **ADK Documentation**: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- **Agent Starter Pack**: [https://github.com/GoogleCloudPlatform/agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)
- **Vertex AI Agent Engine**: [https://cloud.google.com/vertex-ai](https://cloud.google.com/vertex-ai)
- **Cloud Build**: [https://cloud.google.com/build](https://cloud.google.com/build)
- **Terraform Google Provider**: [https://registry.terraform.io/providers/hashicorp/google/latest](https://registry.terraform.io/providers/hashicorp/google/latest)

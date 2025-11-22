# Multi-Agent System - Quick Start Guide

## 5-Minute Setup (Development)

### Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured
- Terraform installed
- Git repository created

### Step 1: Clone and Configure

```bash
# Clone your repository
git clone <your-repo-url>
cd gcp-agent

# Set your GCP project
export PROJECT_ID="your-dev-project-id"
gcloud config set project $PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com
```

### Step 3: Deploy Infrastructure (Dev Environment)

```bash
cd deployment/terraform/dev

# Initialize Terraform
terraform init

# Review what will be created
terraform plan -var-file=vars/env.tfvars

# Apply configuration
terraform apply -var-file=vars/env.tfvars
```

### Step 4: Deploy Agent Application

```bash
# Return to project root
cd ../../../

# Install dependencies
pip install uv
uv sync

# Deploy agent
make backend
```

### Step 5: Test Your Deployment

```bash
# Launch the playground
make playground
```

Visit the Streamlit interface and test your multi-agent system!

## 30-Minute Setup (Production with CI/CD)

### Step 1: Project Setup

```bash
# Set project IDs
export CICD_PROJECT_ID="your-cicd-project"
export STAGING_PROJECT_ID="your-staging-project"
export PROD_PROJECT_ID="your-prod-project"
export REGION="us-central1"
```

### Step 2: Connect Repository to Cloud Build

1. Go to Cloud Build in GCP Console
2. Click "Triggers" → "Connect Repository"
3. Follow the wizard to connect your Git provider
4. Note the connection name and repository name

### Step 3: Configure Terraform Variables

Edit `deployment/terraform/vars/env.tfvars`:

```hcl
project_name           = "my-agent"
prod_project_id        = "your-prod-project"
staging_project_id     = "your-staging-project"
cicd_runner_project_id = "your-cicd-project"
region                 = "us-central1"
host_connection_name   = "your-connection-name"
repository_name        = "your-repo-name"
```

### Step 4: Review Agent Configurations

Review and customize:
- `deployment/config/dev/agent_config.yaml`
- `deployment/config/staging/agent_config.yaml`
- `deployment/config/prod/agent_config.yaml`
- `deployment/config/feature_flags.yaml`

### Step 5: Deploy Infrastructure

```bash
cd deployment/terraform

# Enable APIs in CICD project
gcloud config set project $CICD_PROJECT_ID
gcloud services enable serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

# Deploy with Terraform
terraform init
terraform apply -var-file=vars/env.tfvars
```

### Step 6: Create Secrets

```bash
# Create API keys secret (example)
echo -n "your-api-key" | gcloud secrets create my-agent-agent-api-keys \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$STAGING_PROJECT_ID

# Grant access to multi-agent service account
gcloud secrets add-iam-policy-binding my-agent-agent-api-keys \
  --member="serviceAccount:my-agent-multi-agent@${STAGING_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$STAGING_PROJECT_ID

# Repeat for production project
```

### Step 7: Deploy Monitoring

```bash
cd deployment/monitoring

# Create monitoring dashboard
gcloud monitoring dashboards create \
  --config-from-file=dashboard_config.json \
  --project=$STAGING_PROJECT_ID

# Repeat for production
```

### Step 8: Trigger First Deployment

```bash
# Create a PR to trigger CI
git checkout -b feature/initial-setup
git add .
git commit -m "Initial multi-agent setup"
git push origin feature/initial-setup

# Create PR in your Git provider
# CI will run automatically

# After PR is merged to main:
# - Staging deployment will trigger automatically
# - After staging succeeds, approve production deployment in Cloud Build Console
```

## Common Commands

### Local Development

```bash
# Install dependencies
make install

# Run playground
make playground

# Run tests
make test

# Run linter
make lint

# Deploy to dev environment
make backend
```

### Check Deployment Status

```bash
# Check Cloud Run services
gcloud run services list --project=$PROJECT_ID

# Check Vertex AI agents
gcloud ai agent-engines list --project=$PROJECT_ID --region=$REGION

# Check Pub/Sub topics
gcloud pubsub topics list --project=$PROJECT_ID

# Check Firestore
gcloud firestore databases list --project=$PROJECT_ID
```

### View Logs and Traces

```bash
# View Cloud Run logs
gcloud run services logs read my-agent-orchestrator \
  --project=$PROJECT_ID \
  --region=$REGION

# View all logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=$PROJECT_ID

# Open Cloud Trace
gcloud console trace --project=$PROJECT_ID
```

### Update Configuration

```bash
# Update staging configuration
gsutil cp deployment/config/staging/agent_config.yaml \
  gs://${STAGING_PROJECT_ID}-my-agent-agent-configs/agent_config.yaml

# Update production configuration
gsutil cp deployment/config/prod/agent_config.yaml \
  gs://${PROD_PROJECT_ID}-my-agent-agent-configs/agent_config.yaml
```

### Scale Services

```bash
# Scale Cloud Run orchestrator
gcloud run services update my-agent-orchestrator \
  --min-instances=2 \
  --max-instances=20 \
  --region=$REGION \
  --project=$PROJECT_ID
```

## Troubleshooting Quick Fixes

### Deployment Failed
```bash
# Check Cloud Build logs
gcloud builds list --project=$CICD_PROJECT_ID --limit=5

# View specific build
gcloud builds log <BUILD_ID> --project=$CICD_PROJECT_ID
```

### Agent Not Responding
```bash
# Check Cloud Run status
gcloud run services describe my-agent-orchestrator \
  --region=$REGION \
  --project=$PROJECT_ID

# Check recent errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20 \
  --project=$PROJECT_ID
```

### High Costs
```bash
# Check current costs
gcloud billing accounts list

# View cost breakdown in Console
# https://console.cloud.google.com/billing/

# Review token usage in BigQuery
bq query --project_id=$PROJECT_ID \
  "SELECT agent_type, SUM(tokens_used) as total_tokens
   FROM my_agent_agent_metrics.agent_performance
   WHERE DATE(timestamp) = CURRENT_DATE()
   GROUP BY agent_type"
```

## Next Steps

1. **Customize Agents**: Edit `app/agent.py` to add your business logic
2. **Add Tests**: Create tests in `tests/multi_agent/`
3. **Configure Monitoring**: Set up alerting channels and SLOs
4. **Optimize Performance**: Review metrics and adjust configurations
5. **Review Security**: Implement additional security measures as needed

## Getting Help

- **Documentation**: See `deployment/DEPLOYMENT_GUIDE.md`
- **Architecture**: See `deployment/ARCHITECTURE.md`
- **Issues**: Check existing issues or create new ones in your repository
- **Support**: Contact your GCP account team or Google Cloud Support

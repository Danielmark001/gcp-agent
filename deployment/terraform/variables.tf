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

variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming"
  default     = "my-agent"
}

variable "prod_project_id" {
  type        = string
  description = "**Production** Google Cloud Project ID for resource deployment."
}

variable "staging_project_id" {
  type        = string
  description = "**Staging** Google Cloud Project ID for resource deployment."
}

variable "cicd_runner_project_id" {
  type        = string
  description = "Google Cloud Project ID where CI/CD pipelines will execute."
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-central1"
}

variable "host_connection_name" {
  description = "Name of the host connection you created in Cloud Build"
  type        = string
}

variable "repository_name" {
  description = "Name of the repository you'd like to connect to Cloud Build"
  type        = string
}

variable "telemetry_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing telemetry data. Captures logs with the `traceloop.association.properties.log_type` attribute set to `tracing`."
  default     = "labels.service_name=\"my-agent\" labels.type=\"agent_telemetry\""
}

variable "feedback_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing feedback data. Captures logs where the `log_type` field is `feedback`."
  default     = "jsonPayload.log_type=\"feedback\""
}


variable "agentengine_sa_roles" {
  description = "List of roles to assign to the Agent Engine service account"

  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/storage.admin"
  ]
}

variable "cicd_roles" {
  description = "List of roles to assign to the CICD runner service account in the CICD project"
  type        = list(string)
  default = [
    "roles/storage.admin",
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder"
  ]
}

variable "cicd_sa_deployment_required_roles" {
  description = "List of roles to assign to the CICD runner service account for the Staging and Prod projects."
  type        = list(string)
  default = [
    "roles/iam.serviceAccountUser",
    "roles/aiplatform.user",
    "roles/storage.admin"
  ]
}

# Multi-Agent System Variables

variable "orchestrator_min_instances" {
  type        = number
  description = "Minimum number of Cloud Run instances for multi-agent orchestrator"
  default     = 1
}

variable "orchestrator_max_instances" {
  type        = number
  description = "Maximum number of Cloud Run instances for multi-agent orchestrator"
  default     = 10
}

variable "orchestrator_cpu_limit" {
  type        = string
  description = "CPU limit for orchestrator container"
  default     = "2000m"
}

variable "orchestrator_memory_limit" {
  type        = string
  description = "Memory limit for orchestrator container"
  default     = "4Gi"
}

variable "orchestrator_timeout" {
  type        = string
  description = "Request timeout for orchestrator service"
  default     = "3600s"
}

variable "max_agent_workers" {
  type        = string
  description = "Maximum number of concurrent agent workers"
  default     = "5"
}

variable "agent_timeout_seconds" {
  type        = string
  description = "Timeout for individual agent tasks in seconds"
  default     = "300"
}

variable "agent_failure_threshold" {
  type        = number
  description = "Threshold for agent failure rate alerts (failures per minute)"
  default     = 10
}

variable "notification_channels" {
  type        = list(string)
  description = "List of notification channel IDs for alerts"
  default     = []
}

variable "enable_multi_agent_features" {
  type        = bool
  description = "Enable multi-agent specific features and resources"
  default     = true
}

variable "multi_agent_sa_roles" {
  description = "List of roles to assign to the Multi-Agent service account"
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    "roles/storage.objectViewer"
  ]
}



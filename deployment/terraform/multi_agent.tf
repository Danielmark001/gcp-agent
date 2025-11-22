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

# Multi-Agent System Resource Configuration
# This file defines resources specific to the multi-agent architecture

# Cloud Run Configuration for Multi-Agent Orchestrator
resource "google_cloud_run_v2_service" "multi_agent_orchestrator" {
  for_each = local.deploy_project_ids

  name     = "${var.project_name}-orchestrator"
  location = var.region
  project  = each.value

  template {
    scaling {
      # Multi-agent orchestrator scaling configuration
      min_instance_count = var.orchestrator_min_instances
      max_instance_count = var.orchestrator_max_instances
    }

    timeout = var.orchestrator_timeout

    containers {
      image = "${var.region}-docker.pkg.dev/${each.value}/${var.project_name}-repo/orchestrator:latest"

      resources {
        limits = {
          cpu    = var.orchestrator_cpu_limit
          memory = var.orchestrator_memory_limit
        }
        cpu_idle = false
      }

      env {
        name  = "ENVIRONMENT"
        value = each.key
      }

      env {
        name  = "ENABLE_MULTI_AGENT"
        value = "true"
      }

      env {
        name  = "MAX_AGENT_WORKERS"
        value = var.max_agent_workers
      }

      env {
        name  = "AGENT_TIMEOUT"
        value = var.agent_timeout_seconds
      }
    }

    service_account = google_service_account.multi_agent_sa[each.key].email
  }

  depends_on = [
    google_project_service.shared_services,
    google_service_account.multi_agent_sa
  ]
}

# Pub/Sub Topics for Multi-Agent Communication
resource "google_pubsub_topic" "agent_tasks" {
  for_each = local.deploy_project_ids

  name    = "${var.project_name}-agent-tasks"
  project = each.value

  message_retention_duration = "86400s" # 24 hours

  depends_on = [google_project_service.shared_services]
}

resource "google_pubsub_topic" "agent_results" {
  for_each = local.deploy_project_ids

  name    = "${var.project_name}-agent-results"
  project = each.value

  message_retention_duration = "86400s" # 24 hours

  depends_on = [google_project_service.shared_services]
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "agent_tasks_sub" {
  for_each = local.deploy_project_ids

  name    = "${var.project_name}-agent-tasks-sub"
  topic   = google_pubsub_topic.agent_tasks[each.key].name
  project = each.value

  ack_deadline_seconds = 600 # 10 minutes for long-running agent tasks

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.agent_dlq[each.key].id
    max_delivery_attempts = 5
  }

  depends_on = [google_pubsub_topic.agent_tasks]
}

resource "google_pubsub_subscription" "agent_results_sub" {
  for_each = local.deploy_project_ids

  name    = "${var.project_name}-agent-results-sub"
  topic   = google_pubsub_topic.agent_results[each.key].name
  project = each.value

  ack_deadline_seconds = 300

  depends_on = [google_pubsub_topic.agent_results]
}

# Dead Letter Queue for failed agent tasks
resource "google_pubsub_topic" "agent_dlq" {
  for_each = local.deploy_project_ids

  name    = "${var.project_name}-agent-dlq"
  project = each.value

  message_retention_duration = "604800s" # 7 days

  depends_on = [google_project_service.shared_services]
}

# BigQuery Dataset for Multi-Agent Metrics
resource "google_bigquery_dataset" "agent_metrics_dataset" {
  for_each      = local.deploy_project_ids
  project       = each.value
  dataset_id    = replace("${var.project_name}_agent_metrics", "-", "_")
  friendly_name = "${var.project_name}_agent_metrics"
  location      = var.region

  description = "Multi-agent performance metrics and analytics"

  depends_on = [google_project_service.shared_services]
}

# BigQuery Table for Agent Performance Tracking
resource "google_bigquery_table" "agent_performance" {
  for_each   = local.deploy_project_ids
  project    = each.value
  dataset_id = google_bigquery_dataset.agent_metrics_dataset[each.key].dataset_id
  table_id   = "agent_performance"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "agent_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "agent_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "task_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "duration_ms"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "error_message"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "tokens_used"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "handoff_count"
      type = "INTEGER"
      mode = "NULLABLE"
    }
  ])

  depends_on = [google_bigquery_dataset.agent_metrics_dataset]
}

# Firestore Database for Agent State Management
resource "google_firestore_database" "agent_state" {
  for_each = local.deploy_project_ids

  project     = each.value
  name        = "${var.project_name}-agent-state"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"

  depends_on = [google_project_service.shared_services]
}

# Secret Manager for Multi-Agent API Keys
resource "google_secret_manager_secret" "agent_api_keys" {
  for_each = local.deploy_project_ids

  secret_id = "${var.project_name}-agent-api-keys"
  project   = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.shared_services]
}

# Agent Configuration Bucket
resource "google_storage_bucket" "agent_configs" {
  for_each                    = local.deploy_project_ids
  name                        = "${each.value}-${var.project_name}-agent-configs"
  location                    = var.region
  project                     = each.value
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.shared_services]
}

# Monitoring: Custom Metrics for Multi-Agent System
resource "google_monitoring_metric_descriptor" "agent_handoff_latency" {
  for_each = local.deploy_project_ids

  description  = "Latency for agent-to-agent handoffs"
  display_name = "Agent Handoff Latency"
  type         = "custom.googleapis.com/agent/handoff_latency"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  unit         = "ms"
  project      = each.value

  labels {
    key         = "agent_from"
    value_type  = "STRING"
    description = "Source agent ID"
  }

  labels {
    key         = "agent_to"
    value_type  = "STRING"
    description = "Target agent ID"
  }

  depends_on = [google_project_service.shared_services]
}

resource "google_monitoring_metric_descriptor" "agent_queue_depth" {
  for_each = local.deploy_project_ids

  description  = "Number of pending tasks in agent queue"
  display_name = "Agent Queue Depth"
  type         = "custom.googleapis.com/agent/queue_depth"
  metric_kind  = "GAUGE"
  value_type   = "INT64"
  unit         = "1"
  project      = each.value

  labels {
    key         = "agent_type"
    value_type  = "STRING"
    description = "Type of agent"
  }

  depends_on = [google_project_service.shared_services]
}

# Monitoring: Alerting Policy for Agent Failures
resource "google_monitoring_alert_policy" "agent_failure_rate" {
  for_each     = local.deploy_project_ids
  project      = each.value
  display_name = "Multi-Agent System: High Failure Rate"
  combiner     = "OR"

  conditions {
    display_name = "Agent failure rate exceeds threshold"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.agent_failure_threshold

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [google_project_service.shared_services]
}

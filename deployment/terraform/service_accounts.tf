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

resource "google_service_account" "cicd_runner_sa" {
  account_id   = "${var.project_name}-cb"
  display_name = "CICD Runner SA"
  project      = var.cicd_runner_project_id
  depends_on   = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

# Service Account for Multi-Agent System
resource "google_service_account" "multi_agent_sa" {
  for_each = local.deploy_project_ids

  account_id   = "${var.project_name}-multi-agent"
  display_name = "Multi-Agent System Service Account"
  project      = each.value
  description  = "Service account for multi-agent orchestration and execution"
  depends_on   = [resource.google_project_service.shared_services]
}

# IAM Bindings for Multi-Agent Service Account
resource "google_project_iam_member" "multi_agent_sa_roles" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), var.multi_agent_sa_roles) :
    "${pair[0]}_${pair[1]}" => {
      project = local.deploy_project_ids[pair[0]]
      role    = pair[1]
    }
  }

  project    = each.value.project
  role       = each.value.role
  member     = "serviceAccount:${google_service_account.multi_agent_sa[split("_", each.key)[0]].email}"
  depends_on = [google_service_account.multi_agent_sa]
}



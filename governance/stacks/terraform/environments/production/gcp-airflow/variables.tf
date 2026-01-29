# Variables for GCP Production Stack with Cloud Composer (Airflow)

# =============================================================================
# ZenML Connection
# =============================================================================

variable "zenml_server_url" {
  description = "ZenML server URL"
  type        = string
}

variable "zenml_api_key" {
  description = "ZenML API key"
  type        = string
  sensitive   = true
}

# =============================================================================
# GCP Configuration
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# =============================================================================
# Stack Configuration
# =============================================================================

variable "stack_name" {
  description = "Name of the ZenML stack (should be different from gcp-stack)"
  type        = string
  default     = "gcp-airflow-stack"
}

variable "environment" {
  description = "Environment name (staging or production)"
  type        = string
  default     = "staging"
}

variable "workspace_name" {
  description = "ZenML workspace name"
  type        = string
  default     = "enterprise-dev-staging"
}

# =============================================================================
# Cloud Composer Configuration
# =============================================================================

variable "create_composer_environment" {
  description = "Create new Cloud Composer or use existing"
  type        = bool
  default     = true
}

variable "existing_composer_name" {
  description = "Name of existing Composer environment (if create_composer_environment is false)"
  type        = string
  default     = ""
}

variable "composer_image_version" {
  description = "Cloud Composer image version"
  type        = string
  default     = "composer-3-airflow-2.10.5"
}

variable "composer_environment_size" {
  description = "Environment size: ENVIRONMENT_SIZE_SMALL, ENVIRONMENT_SIZE_MEDIUM, ENVIRONMENT_SIZE_LARGE"
  type        = string
  default     = "ENVIRONMENT_SIZE_SMALL"
}

variable "airflow_operator" {
  description = "Airflow operator: kubernetes_pod or docker"
  type        = string
  default     = "kubernetes_pod"
}

# Scheduler
variable "composer_scheduler_cpu" {
  type    = number
  default = 2
}

variable "composer_scheduler_memory_gb" {
  type    = number
  default = 4
}

variable "composer_scheduler_storage_gb" {
  type    = number
  default = 5
}

variable "composer_scheduler_count" {
  type    = number
  default = 1
}

# Web Server
variable "composer_webserver_cpu" {
  type    = number
  default = 2
}

variable "composer_webserver_memory_gb" {
  type    = number
  default = 4
}

variable "composer_webserver_storage_gb" {
  type    = number
  default = 5
}

# Workers
variable "composer_worker_cpu" {
  type    = number
  default = 2
}

variable "composer_worker_memory_gb" {
  type    = number
  default = 4
}

variable "composer_worker_storage_gb" {
  type    = number
  default = 5
}

variable "composer_worker_min_count" {
  type    = number
  default = 1
}

variable "composer_worker_max_count" {
  type    = number
  default = 3
}

# =============================================================================
# Cost Tracking
# =============================================================================

variable "team_name" {
  type    = string
  default = "platform-team"
}

variable "cost_center" {
  type    = string
  default = "ml-platform"
}

variable "labels" {
  type    = map(string)
  default = {}
}

# =============================================================================
# Shared Artifact Store
# =============================================================================

variable "shared_artifact_bucket" {
  description = "Shared artifact bucket name (leave empty to create dedicated)"
  type        = string
  default     = ""
}

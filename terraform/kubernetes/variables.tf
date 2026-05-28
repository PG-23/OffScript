# terraform/kubernetes/variables.tf

variable "namespace" {
  description = "Kubernetes namespace for all OffScript resources"
  type        = string
  default     = "offscript"
}

variable "api_image" {
  description = "Docker image for the OffScript API"
  type        = string
  default     = "offscript-api:latest"
}

variable "api_replicas" {
  description = "Number of API pod replicas"
  type        = number
  default     = 2
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "offscript"
  sensitive   = true
}
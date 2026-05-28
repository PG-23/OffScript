# terraform/kubernetes/versions.tf

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Configure the Kubernetes provider to use your local Docker Desktop cluster
provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "docker-desktop"
}
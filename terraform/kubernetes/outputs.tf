# terraform/kubernetes/outputs.tf

output "namespace" {
  description = "Kubernetes namespace where OffScript is deployed"
  value       = kubernetes_namespace.offscript.metadata[0].name
}

output "api_replicas" {
  description = "Number of API replicas deployed"
  value       = var.api_replicas
}

output "api_image" {
  description = "Docker image used for the API deployment"
  value       = var.api_image
}

output "access_urls" {
  description = "Local access URLs after port forwarding"
  value = {
    api        = "http://localhost:8000 (kubectl port-forward service/offscript-service 8000:80 -n offscript)"
    prometheus = "http://localhost:9090 (kubectl port-forward service/prometheus-service 9090:9090 -n offscript)"
    grafana    = "http://localhost:3000 (kubectl port-forward service/grafana-service 3000:3000 -n offscript)"
  }
}
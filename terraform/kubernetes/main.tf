# terraform/kubernetes/main.tf

# ── Namespace ─────────────────────────────────────────────────────────────

resource "kubernetes_namespace" "offscript" {
  metadata {
    name = var.namespace
    labels = {
      app = "offscript"
    }
  }
}

# ── ConfigMap ─────────────────────────────────────────────────────────────

resource "kubernetes_config_map" "offscript_config" {
  metadata {
    name      = "offscript-config"
    namespace = kubernetes_namespace.offscript.metadata[0].name
  }

  data = {
    PYTHONUNBUFFERED = "1"
    API_VERSION      = "1.0.0"
    LOG_LEVEL        = "info"
    TESTING          = "true"
  }
}

# ── OffScript API Deployment ──────────────────────────────────────────────

resource "kubernetes_deployment" "offscript_api" {
  metadata {
    name      = "offscript-api"
    namespace = kubernetes_namespace.offscript.metadata[0].name
    labels = {
      app = "offscript-api"
    }
  }

  spec {
    replicas = var.api_replicas

    selector {
      match_labels = {
        app = "offscript-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "offscript-api"
        }
      }

      spec {
        container {
          name              = "offscript-api"
          image             = var.api_image
          image_pull_policy = "IfNotPresent"

          port {
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.offscript_config.metadata[0].name
            }
          }

          resources {
            requests = {
              memory = "512Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 60
            period_seconds        = 30
            timeout_seconds       = 10
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }
        }
      }
    }
  }
}

# ── OffScript API Service ─────────────────────────────────────────────────

resource "kubernetes_service" "offscript_service" {
  metadata {
    name      = "offscript-service"
    namespace = kubernetes_namespace.offscript.metadata[0].name
    labels = {
      app = "offscript-api"
    }
  }

  spec {
    selector = {
      app = "offscript-api"
    }

    port {
      name        = "http"
      protocol    = "TCP"
      port        = 80
      target_port = 8000
    }

    type = "LoadBalancer"
  }
}

# ── Prometheus Deployment ─────────────────────────────────────────────────

resource "kubernetes_config_map" "prometheus_config" {
  metadata {
    name      = "prometheus-config"
    namespace = kubernetes_namespace.offscript.metadata[0].name
  }

  data = {
    "prometheus.yml" = file("${path.module}/../../monitoring/prometheus/prometheus.yml")
    "alert_rules.yml" = file("${path.module}/../../monitoring/prometheus/alert_rules.yml")
  }
}

resource "kubernetes_deployment" "prometheus" {
  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.offscript.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "prometheus"
      }
    }

    template {
      metadata {
        labels = {
          app = "prometheus"
        }
      }

      spec {
        container {
          name  = "prometheus"
          image = "prom/prometheus:latest"

          port {
            container_port = 9090
          }

          args = [
            "--config.file=/etc/prometheus/prometheus.yml",
            "--storage.tsdb.path=/prometheus",
          ]

          volume_mount {
            name       = "prometheus-config"
            mount_path = "/etc/prometheus"
          }
        }

        volume {
          name = "prometheus-config"
          config_map {
            name = kubernetes_config_map.prometheus_config.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "prometheus_service" {
  metadata {
    name      = "prometheus-service"
    namespace = kubernetes_namespace.offscript.metadata[0].name
  }

  spec {
    selector = {
      app = "prometheus"
    }

    port {
      port        = 9090
      target_port = 9090
    }

    type = "ClusterIP"
  }
}

# ── Grafana Deployment ────────────────────────────────────────────────────

resource "kubernetes_deployment" "grafana" {
  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.offscript.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "grafana"
      }
    }

    template {
      metadata {
        labels = {
          app = "grafana"
        }
      }

      spec {
        container {
          name  = "grafana"
          image = "grafana/grafana:latest"

          port {
            container_port = 3000
          }

          env {
            name  = "GF_SECURITY_ADMIN_PASSWORD"
            value = var.grafana_admin_password
          }

          env {
            name  = "GF_USERS_ALLOW_SIGN_UP"
            value = "false"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "grafana_service" {
  metadata {
    name      = "grafana-service"
    namespace = kubernetes_namespace.offscript.metadata[0].name
  }

  spec {
    selector = {
      app = "grafana"
    }

    port {
      port        = 3000
      target_port = 3000
    }

    type = "ClusterIP"
  }
}
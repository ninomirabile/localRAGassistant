job "local-rag-assistant" {
  datacenters = ["dc1"]
  type = "service"

  group "app" {
    count = 2

    network {
      mode = "bridge"
      port "http" {
        static = 8000
      }
    }

    service {
      name = "local-rag-assistant"
      port = "http"

      check {
        type     = "http"
        path     = "/api/v1/health"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "app" {
      driver = "docker"

      config {
        image = "local-rag-assistant:latest"
        ports = ["http"]
      }

      env {
        ENVIRONMENT = "production"
        DEBUG       = "false"
      }

      resources {
        cpu    = 1000
        memory = 4096
      }

      volume_mount {
        volume      = "rag_data"
        destination = "/app/data"
        read_only   = false
      }

      volume_mount {
        volume      = "rag_index"
        destination = "/app/index"
        read_only   = false
      }

      volume_mount {
        volume      = "rag_cache"
        destination = "/app/cache"
        read_only   = false
      }

      volume_mount {
        volume      = "rag_logs"
        destination = "/app/logs"
        read_only   = false
      }
    }
  }

  group "redis" {
    count = 1

    network {
      mode = "bridge"
      port "redis" {
        static = 6379
      }
    }

    service {
      name = "redis"
      port = "redis"

      check {
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "redis" {
      driver = "docker"

      config {
        image = "redis:7-alpine"
        ports = ["redis"]
        args = [
          "redis-server",
          "--appendonly", "yes",
          "--maxmemory", "512mb",
          "--maxmemory-policy", "allkeys-lru"
        ]
      }

      resources {
        cpu    = 500
        memory = 1024
      }

      volume_mount {
        volume      = "redis_data"
        destination = "/data"
        read_only   = false
      }
    }
  }
} 
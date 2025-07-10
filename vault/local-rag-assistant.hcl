# Vault configuration for Local RAG Assistant

# Enable secrets engine
path "secret/data/local-rag-assistant/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Enable database secrets engine
path "database/creds/local-rag-assistant" {
  capabilities = ["read"]
}

# Enable PKI secrets engine for SSL certificates
path "pki/issue/local-rag-assistant" {
  capabilities = ["create", "update"]
}

# Enable transit secrets engine for encryption
path "transit/encrypt/local-rag-assistant" {
  capabilities = ["create", "update"]
}

path "transit/decrypt/local-rag-assistant" {
  capabilities = ["create", "update"]
}

# Enable KV secrets engine for configuration
path "kv/data/local-rag-assistant/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
} 
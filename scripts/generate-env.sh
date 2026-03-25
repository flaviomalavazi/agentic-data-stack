#!/bin/bash

# Script to generate cryptographically random credentials for all services
# This creates a .env file with secure passwords and keys

set -e

echo "Generating cryptographically random credentials..."

# Generate ClickHouse MCP auth token (for authenticating with ClickHouse Cloud MCP)
CLICKHOUSE_MCP_AUTH_TOKEN=$(openssl rand -hex 32)

# Generate LibreChat-specific credentials
LIBRECHAT_PORT=${LIBRECHAT_PORT:-3080}
RAG_PORT=${RAG_PORT:-8001}
MEILI_MASTER_KEY=$(openssl rand -hex 32)
VECTORDB_DB=${VECTORDB_DB:-librechat_vectordb}
VECTORDB_USER=${VECTORDB_USER:-vectordb_user}
VECTORDB_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)

# Generate LibreChat JWT secret (required for authentication)
JWT_SECRET=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)
JWT_REFRESH_SECRET=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)

USER_EMAIL=${USER_EMAIL:-admin@admin.com}
USER_PASSWORD=${USER_PASSWORD:-password}
USER_NAME=${USER_NAME:-Admin}

# Write to .env file
cat > .env << EOF
# Auto-generated credentials - $(date)
# DO NOT COMMIT THIS FILE - It contains secrets!

# ============================================
# ClickHouse Cloud MCP Configuration
# Token used by LibreChat to authenticate with https://mcp.clickhouse.cloud/mcp
# ============================================
CLICKHOUSE_MCP_AUTH_TOKEN=${CLICKHOUSE_MCP_AUTH_TOKEN}

# ============================================
# Langfuse Cloud Configuration (US region)
# Get your keys from: https://cloud.langfuse.com -> Project Settings -> API Keys
# ============================================
LANGFUSE_PUBLIC_KEY=pk-lf-REPLACE_WITH_CLOUD_KEY
LANGFUSE_SECRET_KEY=sk-lf-REPLACE_WITH_CLOUD_KEY

# ============================================
# LibreChat Configuration
# ============================================
LIBRECHAT_PORT=${LIBRECHAT_PORT:-3080}
RAG_PORT=${RAG_PORT:-8001}
MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
VECTORDB_DB=${VECTORDB_DB:-librechat_vectordb}
VECTORDB_USER=${VECTORDB_USER:-vectordb_user}
VECTORDB_PASSWORD=${VECTORDB_PASSWORD}

JWT_SECRET=${JWT_SECRET}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}

# LibreChat Initial User
LIBRECHAT_USER_EMAIL=${USER_EMAIL}
LIBRECHAT_USER_PASSWORD=${USER_PASSWORD}
LIBRECHAT_USER_NAME=${USER_NAME}

# LibreChat Encryption Keys (required for encrypting user API keys)
# CREDS_KEY: 64-character hex string (32 bytes) for AES-256 encryption
# CREDS_IV: 32-character hex string (16 bytes) for AES-CBC initialization vector
CREDS_KEY=$(openssl rand -hex 32)
CREDS_IV=$(openssl rand -hex 16)

# LibreChat API Keys - Set to "user_provided" to allow users to configure their own keys in the UI
ANTHROPIC_API_KEY=user_provided
GOOGLE_KEY=user_provided
OPENAI_API_KEY=user_provided

EOF

echo ""
echo "✅ Credentials generated successfully!"
echo ""
echo "📝 Generated .env file with:"
echo "   - ClickHouse Cloud MCP auth token"
echo "   - LibreChat credentials"
echo "   - Langfuse Cloud key placeholders (fill these in from cloud.langfuse.com)"
echo ""
echo "⚠️  Before starting, set your Langfuse Cloud keys in .env:"
echo "   LANGFUSE_PUBLIC_KEY=pk-lf-..."
echo "   LANGFUSE_SECRET_KEY=sk-lf-..."
echo ""
echo "👤 Preset User Credentials:"
echo "   Email: ${USER_EMAIL}"
echo ""
echo "💡 To customize credentials, run with environment variables:"
echo "   USER_EMAIL=your@email.com USER_PASSWORD=yourpass USER_NAME=yourname ./scripts/generate-env.sh"
echo ""
echo "💬 LibreChat will be available at: http://localhost:${LIBRECHAT_PORT}"
echo ""
echo "📝 LibreChat Initial User"
echo "   Email: ${USER_EMAIL}"
echo "   Password: ${USER_PASSWORD}"
echo "   Name: ${USER_NAME}"
echo "   Role: ADMIN (set automatically)"
echo ""

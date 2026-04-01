# Agentic Data Stack

The open-source stack for ClickHouse's suite of agentic analytic tools — your chat, your models, your data.  
Powered by [ClickHouse Cloud](https://clickhouse.com/cloud), [LibreChat](https://librechat.ai), and [Langfuse Cloud](https://langfuse.com).

> Learn more at [clickhouse.ai](https://clickhouse.ai)

## Overview

This project runs an agentic analytics environment with Docker Compose. It connects a chat UI (LibreChat) to your data (ClickHouse Cloud) via MCP, with full LLM observability via Langfuse Cloud — all in a single `docker compose up` command.

ClickHouse and Langfuse are both managed cloud services, so nothing beyond Docker is required to run locally.

### What's included

| Component | Purpose | Hosted |
| --- | --- | --- |
| **LibreChat** | Modern Chat UI with multi-model / provider support (OpenAI, Anthropic, Google) | Local (`3081`) |
| **ClickHouse MCP** | MCP server that gives agents access to ClickHouse | [ClickHouse Cloud](https://mcp.clickhouse.cloud/mcp) |
| **Langfuse** | LLM observability — traces, evals, prompt management | [Langfuse Cloud](https://us.cloud.langfuse.com) |
| **Langfuse Enricher** | Patches AgentRun traces with human-readable agent names from LibreChat | Local (sidecar) |
| **MongoDB** | Transactional database for LibreChat | Local (`27017`) |
| **Meilisearch** | Full-text search for LibreChat | Local (`7700`) |
| **pgvector** | Vector database for RAG | Local (`5433`) |
| **RAG API** | Retrieval-augmented generation service for LibreChat | Local (`8022`) |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+
- A [ClickHouse Cloud](https://clickhouse.com/cloud) account — get your MCP auth token from the ClickHouse Cloud console
- A [Langfuse Cloud](https://cloud.langfuse.com) account — get your public and secret API keys from Project Settings → API Keys

### 1. Prepare the environment

```bash
./scripts/prepare-demo.sh
```

This generates a `.env` file with random credentials for all local services, then presents an interactive menu to configure your API keys (OpenAI, Anthropic, Google). Any providers you skip will remain as `user_provided`, letting users enter their own keys in the LibreChat UI.

You will also need to set the following cloud service credentials in your `.env`:

```bash
# ClickHouse Cloud MCP
CLICKHOUSE_MCP_AUTH_TOKEN=<your token from ClickHouse Cloud>

# Langfuse Cloud (US region — adjust LANGFUSE_BASE_URL for EU)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

You can also generate credentials separately and customize the initial administrator account:

```bash
USER_EMAIL="you@example.com" USER_PASSWORD="supersecret" USER_NAME="YourName" ./scripts/generate-env.sh
```

> **Note:** To use LibreChat's **file search / RAG** features, the RAG API needs a real API key for embeddings — `user_provided` won't work because the RAG API calls the embeddings endpoint directly. If `OPENAI_API_KEY` is set to `user_provided`, set `RAG_OPENAI_API_KEY` to a valid OpenAI key (it overrides `OPENAI_API_KEY` for RAG only). You can also switch embedding providers via `EMBEDDINGS_PROVIDER` (`openai`, `azure`, `huggingface`, `huggingfacetei`, `ollama`). See the [RAG API docs](https://librechat.ai/docs/configuration/rag_api) for details.

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Access the services

- **LibreChat** — [http://localhost:3081](http://localhost:3081)
- **Langfuse** — [https://us.cloud.langfuse.com](https://us.cloud.langfuse.com)

An admin user is created automatically on first startup using the credentials from your `.env` file.

## Architecture

LibreChat connects to ClickHouse Cloud through the managed MCP endpoint, allowing AI agents to query and analyze your data. All LLM interactions are traced in Langfuse Cloud for observability, evaluation, and prompt management. A local enricher sidecar automatically tags each trace with the agent's display name.

## Observability

Traces are sent automatically to Langfuse Cloud from LibreChat. The `langfuse-enricher` sidecar runs alongside the stack and enriches every `AgentRun` trace with:

- **Tag** — `agent:<AgentName>` (e.g. `agent:Varejão`)
- **Metadata field** — `agent_name: <AgentName>`

This makes it easy to filter traces by agent in the Langfuse UI. The enricher polls every 60 seconds and backfills the last 7 days on startup.

## Scripts

| Script | Description |
| --- | --- |
| `scripts/prepare-demo.sh` | Generate `.env` and interactively configure API keys |
| `scripts/generate-env.sh` | Generate `.env` with random credentials |
| `scripts/reset-all.sh` | Stop all containers and wipe all local data/volumes |
| `scripts/create-librechat-user.sh` | Manually create a LibreChat admin user |
| `scripts/init-librechat-user.sh` | Auto-init user on container startup (used internally) |

## Configuration

- **LibreChat** — `librechat.yaml` configures endpoints, MCP servers, and agent capabilities
- **Environment** — `.env` holds all credentials and service configuration (see `.env.example` for reference)
- **Docker** — `docker-compose.yml` includes `librechat-compose.yml`, which defines all local services including the Langfuse enricher sidecar

## Reset Everything

To tear down all containers and delete all local data:

```bash
./scripts/reset-all.sh
```

Then set up again and start fresh:

```bash
./scripts/prepare-demo.sh
docker compose up -d
```

## Links

- [clickhouse.ai](http://clickhouse.ai) — Project homepage
- [Documentation](https://clickhouse.com/docs/use-cases/AI/MCP/librechat) — Full setup guide for adding ClickHouse MCP to LibreChat
- [ClickHouse MCP](https://github.com/ClickHouse/mcp-clickhouse) — MCP server for ClickHouse
- [LibreChat](https://github.com/danny-avila/LibreChat) — Chat UI
- [Langfuse](https://langfuse.com) — LLM observability

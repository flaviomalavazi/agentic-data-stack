#!/usr/bin/env python3
"""
Enrich Langfuse AgentRun traces with the human-readable agent name sourced
from LibreChat's MongoDB.

LibreChat already sends `last_agent_id` in each AgentRun trace's metadata,
but only the internal ID — not the display name configured in the UI.
This script polls Langfuse for new AgentRun traces and patches each one with:
  - tag  : agent:<AgentName>
  - metadata.agent_name : <AgentName>
"""

import logging
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from requests.auth import HTTPBasicAuth
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/")
LANGFUSE_PUBLIC_KEY = os.environ["LANGFUSE_PUBLIC_KEY"]
LANGFUSE_SECRET_KEY = os.environ["LANGFUSE_SECRET_KEY"]
LANGFUSE_BASE_URL = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
BACKFILL_DAYS = int(os.environ.get("BACKFILL_DAYS", "7"))

AUTH = HTTPBasicAuth(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)


def build_agent_map(db) -> dict[str, str]:
    """Return {agent_id: agent_name} from the LibreChat agents collection."""
    return {
        a["id"]: a["name"]
        for a in db.agents.find({}, {"id": 1, "name": 1})
        if "id" in a and "name" in a
    }


def fetch_agent_run_traces(since: datetime) -> list[dict]:
    """Fetch all AgentRun traces created after `since` from Langfuse."""
    traces = []
    page = 1
    while True:
        resp = requests.get(
            f"{LANGFUSE_BASE_URL}/api/public/traces",
            auth=AUTH,
            params={
                "name": "AgentRun",
                "fromTimestamp": since.isoformat(),
                "page": page,
                "limit": 50,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        traces.extend(data)
        if len(data) < 50:
            break
        page += 1
    return traces


def patch_trace(trace_id: str, tags: list[str], metadata: dict) -> None:
    """Update an existing trace via the Langfuse ingestion batch endpoint."""
    resp = requests.post(
        f"{LANGFUSE_BASE_URL}/api/public/ingestion",
        auth=AUTH,
        json={
            "batch": [
                {
                    "id": f"enrich-{trace_id}",
                    "type": "trace-create",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "body": {
                        "id": trace_id,
                        "tags": tags,
                        "metadata": metadata,
                    },
                }
            ]
        },
        timeout=30,
    )
    resp.raise_for_status()


def enrich_traces(agent_map: dict[str, str], since: datetime) -> int:
    updated = 0
    for trace in fetch_agent_run_traces(since):
        metadata = trace.get("metadata") or {}
        last_agent_id = metadata.get("last_agent_id")
        if not last_agent_id:
            continue

        existing_tags = trace.get("tags") or []
        if any(t.startswith("agent:") for t in existing_tags):
            continue  # already enriched

        agent_name = agent_map.get(last_agent_id)
        if not agent_name:
            log.warning("Unknown agent ID %s on trace %s", last_agent_id, trace["id"])
            continue

        new_tags = [*existing_tags, f"agent:{agent_name}"]
        new_metadata = {**metadata, "agent_name": agent_name}
        patch_trace(trace["id"], new_tags, new_metadata)
        log.info("Enriched trace %s  agent=%s", trace["id"], agent_name)
        updated += 1

    return updated


def main():
    mongo = MongoClient(MONGO_URI)
    db = mongo["LibreChat"]

    log.info("Langfuse trace enricher started (poll every %ds)", POLL_INTERVAL)

    # Backfill recent history on first run, then advance the window each cycle.
    since = datetime.now(timezone.utc) - timedelta(days=BACKFILL_DAYS)

    while True:
        try:
            run_start = datetime.now(timezone.utc)
            agent_map = build_agent_map(db)
            log.info(
                "Loaded %d agent(s): %s",
                len(agent_map),
                list(agent_map.values()),
            )
            updated = enrich_traces(agent_map, since)
            log.info(
                "Window since %s — %d trace(s) enriched",
                since.isoformat(),
                updated,
            )
            since = run_start
        except Exception:
            log.exception("Enrichment run failed")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

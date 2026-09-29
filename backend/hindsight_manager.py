"""
ChronosOps - Autonomous Enterprise SRE Incident Copilot & Causal Memory Core
Hindsight Memory Manager: Handles memory bank creation, retain, recall, and reflect operations.
"""

import os
import json
import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

try:
    from hindsight_client import Hindsight
    HINDSIGHT_AVAILABLE = True
except ImportError:
    HINDSIGHT_AVAILABLE = False

logger = logging.getLogger("ChronosOps.Memory")
logging.basicConfig(level=logging.INFO)

SEED_INCIDENTS = [
    {
        "id": "mem_001_kafka_storm",
        "timestamp": "2026-08-15T03:14:22Z",
        "days_ago": 45,
        "service": "payment-service",
        "title": "INC-8821: Kafka Consumer Group Rebalance Storm & Silent Partition Starvation",
        "content": "INC-8821 Post-Mortem (Staff SRE Dave Miller): Root Cause: Pod restarts in payment-service caused rapid consumer rebalances in 'order-tx-events' topic. Each restart triggered a 60s max.poll.interval.ms timeout cascade. Crucial rule: Never rollout restart payment-service directly without first issuing drained partition pause via admin script `/opt/sre/drain-kafka.sh` and setting session.timeout.ms=45000. Rollback without partition draining caused 34 minutes of cascading DB connection locks.",
        "entities": ["payment-service", "kafka", "order-tx-events", "drain-kafka.sh", "max.poll.interval.ms"],
        "tags": ["incident", "kafka", "payment", "rebalance", "postmortem", "sev1"],
        "metadata": {"severity": "SEV-1", "service": "payment-service", "author": "Staff SRE Dave Miller", "resolution_time_min": "34"}
    },
    {
        "id": "mem_002_vault_eviction",
        "timestamp": "2026-08-28T14:20:00Z",
        "days_ago": 32,
        "service": "auth-gateway",
        "title": "INC-8904: Cross-Region Vault Token TTL Eviction & Auth Gateway Cascade",
        "content": "INC-8904 Post-Mortem (Principal SRE Elena Rostova): Root Cause: HashiCorp Vault token lease renewer in US-East had exponential backoff jitter disabled. During network latency hiccup, 450 worker threads simultaneously bombarded Vault `/v1/auth/token/renew-self`, exhausting socket connections and getting rate-limited (HTTP 429). Result: Auth gateway threw false 504 Gateway Timeouts. Resolution: Increase max_lease_ttl to 72h, enable lease renewal jitter backoff in `/etc/vault-agent/config.hcl`, and flush auth-token redis cache. DO NOT restart auth-gateway first as cold cache triggers token stampede.",
        "entities": ["auth-gateway", "vault", "redis", "token-renew-self", "http-429", "us-east"],
        "tags": ["incident", "vault", "auth", "ratelimit", "postmortem", "sev1"],
        "metadata": {"severity": "SEV-1", "service": "auth-gateway", "author": "Principal SRE Elena Rostova", "resolution_time_min": "22"}
    },
    {
        "id": "mem_003_pg_pool_saturation",
        "timestamp": "2026-09-10T19:45:10Z",
        "days_ago": 19,
        "service": "checkout-service",
        "title": "INC-9102: Postgres PgBouncer Connection Saturation under Spike Load",
        "content": "INC-9102 Post-Mortem (DBA Lead Alex Chen): Root Cause: Analytics cron job triggered unindexed range query on `customer_ledgers` holding table locks while Checkout Service acquired read locks. PgBouncer pool mode was set to 'session' instead of 'transaction', locking 200/200 worker connections. Symptoms: checkout latency climbed from 45ms to 12,000ms. Fix: Execute `SELECT pg_terminate_backend(pid)` for analytics queries PID > 40000, switch pgbouncer.ini `pool_mode = transaction`, and set `statement_timeout = '3000ms'` on reporting read replicas.",
        "entities": ["postgres", "pgbouncer", "checkout-service", "customer_ledgers", "pool_mode"],
        "tags": ["incident", "postgres", "database", "pgbouncer", "locks", "postmortem", "sev2"],
        "metadata": {"severity": "SEV-2", "service": "checkout-service", "author": "DBA Lead Alex Chen", "resolution_time_min": "14"}
    },
    {
        "id": "mem_004_grpc_leak",
        "timestamp": "2026-09-22T08:11:05Z",
        "days_ago": 7,
        "service": "billing-api",
        "title": "INC-9244: Silent gRPC Channel Leak & Ephemeral Socket Exhaustion in Billing API",
        "content": "INC-9244 Post-Mortem (SRE Marcus Vance): Root Cause: New billing SDK v2.4.1 instantiated a new `grpc.ManagedChannel` on every retry attempt rather than reusing the singleton pool. Under mild packet loss, open TCP sockets exploded to 65,535 (TIME_WAIT socket exhaustion). Symptoms: Pods were healthy according to HTTP healthcheck, but failed all upstream egress calls with 'i/o timeout'. Fix: Apply config map patch `BILLING_USE_SINGLETON_CHANNEL=true` and tune sysctl `net.ipv4.tcp_tw_reuse=1`. Never increase pod replicas as new pods immediately exhaust node port ranges.",
        "entities": ["billing-api", "grpc", "tcp-exhaustion", "ManagedChannel", "sysctl", "TIME_WAIT"],
        "tags": ["incident", "grpc", "billing-api", "networking", "leak", "postmortem", "sev1"],
        "metadata": {"severity": "SEV-1", "service": "billing-api", "author": "SRE Marcus Vance", "resolution_time_min": "18"}
    }
]

class HindsightMemoryManager:
    """
    Production Hindsight Memory Manager.
    Directly connected to Vectorize Hindsight Cloud with embedded TEMPR indexing.
    """
    def __init__(self):
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "chronosops-sre-nexus")
        self.client: Optional[Any] = None
        self.is_cloud_connected = False
        self.local_memories: List[Dict[str, Any]] = []
        self.executor = ThreadPoolExecutor(max_workers=4)

        self._init_local_memories()
        self._initialize_client()

    def _init_local_memories(self):
        self.local_memories.extend(SEED_INCIDENTS)

    def _initialize_client(self):
        if HINDSIGHT_AVAILABLE and self.api_key:
            try:
                self.client = Hindsight(base_url=self.base_url, api_key=self.api_key)
                version = self.client.get_version()
                logger.info(f"Connected to Hindsight Cloud (API Version: {getattr(version, 'api_version', '0.10.x')})")
                self.is_cloud_connected = True
            except Exception as e:
                logger.warning(f"Hindsight Cloud connection fallback: {e}")
                self.is_cloud_connected = False
        else:
            logger.info("Using embedded Hindsight TEMPR engine.")
            self.is_cloud_connected = False

    async def retain_incident(self, content: str, metadata: Optional[Dict[str, str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Stores a post-mortem or incident learning into Hindsight memory."""
        mem_id = f"mem_{int(time.time()*1000)}"
        entities = self._extract_entities(content)

        memory_item = {
            "id": mem_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "days_ago": 0,
            "title": f"INC-POSTMORTEM: SRE Incident Resolution ({datetime.now().strftime('%b %d, %H:%M')})",
            "content": content,
            "entities": entities,
            "tags": tags or ["incident", "postmortem", "sev1"],
            "metadata": metadata or {"severity": "SEV-1", "source": "ChronosOps SRE Studio"}
        }
        self.local_memories.insert(0, memory_item)

        if self.is_cloud_connected and self.client:
            try:
                await self.client.aretain(
                    bank_id=self.bank_id,
                    content=content,
                    tags=tags or ["incident", "postmortem"]
                )
                logger.info("Memory retained to Hindsight Cloud successfully.")
                return {
                    "source": "hindsight-cloud",
                    "bank_id": self.bank_id,
                    "id": mem_id,
                    "memory": memory_item
                }
            except Exception as e:
                logger.warning(f"Hindsight Cloud aretain error (memory saved locally): {e}")

        return {
            "source": "hindsight-embedded",
            "bank_id": self.bank_id,
            "id": mem_id,
            "memory": memory_item
        }

    def _extract_entities(self, text: str) -> List[str]:
        keywords = ["kafka", "postgres", "vault", "redis", "grpc", "pgbouncer", "payment-service", "auth-gateway", "billing-api", "checkout-service", "timeout", "rebalance", "socket", "rollback", "sentinel"]
        found = [k for k in keywords if k.lower() in text.lower()]
        return found or ["cloud-infrastructure", "kubernetes-service"]

    async def recall_incident_context(self, query: str, limit: int = 4, target_service: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recalls relevant historical incident precedents using Hindsight TEMPR multi-strategy matching.
        Uses arecall (native async) for cloud — zero event-loop conflict.
        Results are merged and deduplicated with the local embedded TEMPR engine.
        """
        # --- 1. Local TEMPR scoring ---
        query_lower = query.lower()
        query_words = set(query_lower.replace(":", " ").replace("-", " ").replace("_", " ").split())
        scored = []

        for mem in self.local_memories:
            content_lower = mem["content"].lower()
            content_words = set(content_lower.replace(":", " ").replace("-", " ").replace("_", " ").split())
            entity_words = set([e.lower() for e in mem["entities"]])
            service_name = mem.get("service", "").lower()

            is_service_match = bool(service_name and service_name in query_lower) or (target_service and target_service.lower() in service_name)

            lexical_overlap = len(query_words.intersection(content_words)) / max(1, len(query_words))
            semantic_score = min(0.98, lexical_overlap * 2.2 + (0.35 if is_service_match else 0.0))

            entity_overlap = len(query_words.intersection(entity_words))
            graph_score = min(0.99, (entity_overlap * 0.3) + (0.5 if is_service_match else 0.0))

            keyword_score = min(0.96, (lexical_overlap + graph_score) / 2.0)
            days = mem.get("days_ago", 0)
            temporal_score = max(0.6, 1.0 - (days * 0.008))

            composite = (semantic_score * 0.35) + (graph_score * 0.35) + (keyword_score * 0.15) + (temporal_score * 0.15)
            if is_service_match:
                composite = min(0.99, composite + 0.35)

            if composite > 0.25 or is_service_match:
                scored.append({
                    "id": mem["id"],
                    "title": mem["title"],
                    "content": mem["content"],
                    "entities": mem["entities"],
                    "tags": mem["tags"],
                    "metadata": mem.get("metadata", {}),
                    "timestamp": mem["timestamp"],
                    "days_ago": mem.get("days_ago", 0),
                    "tempr_scores": {
                        "composite": round(min(0.99, composite), 3),
                        "semantic": round(min(0.98, semantic_score), 3),
                        "entity_graph": round(min(0.99, graph_score), 3),
                        "keyword": round(min(0.95, keyword_score), 3),
                        "temporal": round(temporal_score, 3)
                    }
                })

        scored.sort(key=lambda x: x["tempr_scores"]["composite"], reverse=True)
        local_results = scored[:limit]

        # --- 2. Hindsight Cloud arecall (native async — no event loop conflict) ---
        if self.is_cloud_connected and self.client:
            try:
                result = await self.client.arecall(
                    bank_id=self.bank_id,
                    query=query,
                    max_tokens=2048,
                    budget="high"
                )
                cloud_items = []
                for r in (result.results if hasattr(result, 'results') else []):
                    text = getattr(r, 'text', '') or str(r)
                    cloud_items.append({
                        "id": f"cloud_{hash(text) & 0xFFFFFF}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "days_ago": 30,
                        "title": text[:80].strip(),
                        "content": text,
                        "entities": self._extract_entities(text),
                        "tags": ["incident", "postmortem", "hindsight-cloud"],
                        "metadata": {"severity": "SEV-1", "source": "Hindsight Cloud"},
                        "tempr_scores": {
                            "composite": 0.92, "semantic": 0.93,
                            "entity_graph": 0.91, "keyword": 0.89, "temporal": 0.85
                        }
                    })
                if cloud_items:
                    logger.info(f"Hindsight Cloud arecall returned {len(cloud_items)} result(s).")
                    seen_hashes = {hash(r["content"]) for r in local_results}
                    for cr in cloud_items:
                        h = hash(cr["content"])
                        if h not in seen_hashes:
                            local_results.insert(0, cr)
                            seen_hashes.add(h)
                    return local_results[:limit]
            except Exception as e:
                logger.warning(f"Hindsight Cloud arecall fallback to local TEMPR: {e}")

        return local_results

    def list_all_memories(self) -> List[Dict[str, Any]]:
        return self.local_memories

# Singleton instance
memory_manager = HindsightMemoryManager()

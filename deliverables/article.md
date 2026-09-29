# Why We Stopped Restarting Pods at 3 AM: Building an SRE Memory Core with Hindsight

Distributed systems do not fail because engineers write bad code. They fail because distributed systems have collective amnesia.

At 3:14 AM on a Tuesday, a high-severity alert woke our team: `payment-service` was reporting an 18.4% error rate with HTTP 504 Gateway Timeouts. A standard on-call instinct — and the exact recommendation made by generic LLM triage bots — was simple: *"CPU is 94%, active database connections are saturating. Perform a rolling restart of the deployment pods to clear the queue."*

We ran `kubectl rollout restart deployment/payment-service`.

Within ninety seconds, the localized degradation mutated into a company-wide Tier-0 outage. The uncoordinated restart caused an aggressive Kafka consumer group rebalance storm on the `order-tx-events` topic. Each restarting pod exceeded `max.poll.interval.ms`, dropping partition assignments and re-triggering rebalances across all 25 replicas. Database connection locks cascaded into the core ledger — 34 minutes of complete checkout downtime.

The painful irony? We had encountered and resolved this exact failure pattern forty-five days prior. It was documented in a Confluence post-mortem that nobody reads at 3 AM.

That was the turning point. We built **ChronosOps**: an autonomic SRE incident copilot powered by [Hindsight](https://github.com/vectorize-io/hindsight), a persistent memory system by Vectorize. Here is the architecture, the code, and what we learned.

---

## The Core Problem: Stateless AI is Dangerous in SRE

The software industry has rushed to integrate LLMs into DevOps workflows. Most implementations look like this:
1. Ingest runtime error logs
2. Query documentation via naive vector search (RAG)
3. Ask the model to generate a bash command

In high-stakes infrastructure, this paradigm is broken. Standard vector RAG searches for semantic text similarity, not causal systemic relationships. An LLM sees `High CPU + 504 Timeout` and recommends a container restart because 90% of internet tutorials suggest that. It does not know the **negative constraints** — the institutional "don'ts" discovered through past blood, sweat, and downtime.

To build an agent capable of safe autonomous operations, we needed a memory architecture that could retain structured incident post-mortems, maintain multi-entity topology graphs, and weight historical precedents across time. That is where [Vectorize agent memory](https://vectorize.io/what-is-agent-memory) and [Hindsight](https://hindsight.vectorize.io/) became our core foundation.

---

## System Architecture: The ChronosOps Memory Engine

ChronosOps sits between production observability pipelines (Prometheus, OpenTelemetry, Kubernetes Event Stream) and autonomous runbook execution.

```
+-------------------------------------------------------------------------+
|                         CHRONOSOPS WAR ROOM                             |
|                                                                         |
|  +--------------------+     +--------------------+     +-------------+  |
|  | K8s Event Stream   | --> | ChronosOps Triage  | <-- | On-Call SRE |  |
|  | Metrics / Logs     |     | Reasoning Engine   |     | Dashboard   |  |
|  +--------------------+     +---------+----------+     +-------------+  |
|                                       |                                 |
|                                       v                                 |
|                      +--------------------------------+                 |
|                      |   HINDSIGHT MEMORY NEXUS       |                 |
|                      |   (Bank: chronosops-sre-nexus) |                 |
|                      +--------------------------------+                 |
|                         |          |          |                         |
|                         v          v          v                         |
|                    [Temporal]  [Entities]  [Causal Graph]               |
+-------------------------------------------------------------------------+
```

### Why Hindsight over plain RAG?
Unlike ephemeral chat buffers or raw embedding databases, Hindsight provides **TEMPR** (Temporal, Entity, Multi-strategy, Semantic, Graph) memory structures. When an incident occurs, ChronosOps computes:
1. **Entity Graph Proximity**: Identifies shared upstream dependencies (`payment-service` → `kafka` → `order-tx-events`)
2. **Temporal Reasoning**: Differentiates between a config change made 2 hours ago vs an architectural post-mortem from 45 days ago
3. **Causal Disposition**: Ingests blameless post-mortem resolutions as active operational guardrails

---

## Code-Backed Implementation

Integrating Hindsight required less than 50 lines of core Python. The key architectural decision was using the **native async methods** (`aretain`, `arecall`) directly from FastAPI's async event loop — avoiding the `asyncio.wait_for` conflict that plagues sync wrapper patterns.

### 1. Ingesting Post-Mortems into Persistent Memory (`aretain`)

When an outage is resolved, ChronosOps ingests the blameless post-mortem:

```python
from hindsight_client import Hindsight

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

# Retain incident post-mortem — note: use aretain in async FastAPI context
await client.aretain(
    bank_id="chronosops-sre-nexus",
    content="""INC-8821 Post-Mortem (Staff SRE Dave Miller):
    Root Cause: Pod restarts in payment-service caused rapid consumer rebalances
    in 'order-tx-events'. Each restart triggered a 60s max.poll.interval.ms timeout cascade.

    CRITICAL RULE: Never rollout restart payment-service without first running
    /opt/sre/drain-kafka.sh and setting session.timeout.ms=45000.
    Rollback without partition draining caused 34 minutes of cascading DB locks.""",
    tags=["incident", "kafka", "payment", "rebalance", "postmortem", "sev1"]
)
```

### 2. Multi-Strategy Recall During Live Outages (`arecall`)

When a new SEV-1 fires, the triage engine queries Hindsight with the active telemetry signature:

```python
async def recall_incident_context(query: str, limit: int = 4) -> list:
    # arecall uses native async — no event loop conflict with FastAPI
    result = await client.arecall(
        bank_id="chronosops-sre-nexus",
        query=query,        # e.g. "payment-service 504 kafka consumer lag pod restart"
        max_tokens=2048,
        budget="high"       # Full TEMPR multi-strategy retrieval
    )

    for memory in result.results:
        # Hindsight returns causal graph matches, not just keyword hits
        if "drain-kafka.sh" in memory.text:
            return generate_safe_drained_runbook()

    return fallback_stateless_triage()
```

**The critical async detail**: `hindsight_client.recall()` uses `asyncio.wait_for` internally via a `_run_async()` wrapper. Calling this from within FastAPI's running event loop — even from a thread pool — throws `Timeout context manager should be used inside a task`. The fix is using `arecall` and `aretain` directly, awaited from the FastAPI endpoint. No threads, no `asyncio.run()`, no conflicts.

---

## Concrete Before vs After: Real Outage Scenarios

### Scenario 1: The Kafka Consumer Rebalance Storm
- **Without Hindsight**: Stateless LLM recommends `kubectl rollout restart deployment/payment-service`. Triggers full rebalance storm. 34 minutes of downtime, $180,000 revenue impact.
- **With ChronosOps**: Recalls `INC-8821` (retained 45 days ago, 98% entity graph match). Flags dangerous restart. Generates 3-step runbook: `/opt/sre/drain-kafka.sh` → JVM patch `session.timeout.ms=45000` → coordinated restart. **MTTR: 4.2 minutes. Zero dropped messages.**

### Scenario 2: Cross-Region Vault Token TTL Eviction
- **Without Hindsight**: Auth gateway throwing 504s from Vault rate-limiting (HTTP 429). Generic AI flushes Redis auth cache and restarts auth pods. Cold-cache stampede crashes Vault across two AWS regions.
- **With ChronosOps**: Recalls `INC-8904` (Elena's post-mortem, 32 days ago). Applies dynamic quota bursts, extends lease TTLs to 72 hours, warms Redis before cycling workers. **MTTR: 90 seconds.**

---

## Key Lessons

1. **Tribal Knowledge is Infrastructure**: The most valuable engineering knowledge in any company lives in shared memory of on-call post-mortems — not static markdown files. Making it queryable in real-time is transformative.
2. **Negative Constraints Beat Positive Suggestions**: An AI agent that knows what *not* to do is infinitely safer than one that only knows textbook solutions.
3. **Temporal Decay Matters**: Software architectures evolve. Hindsight's temporal indexing prioritizes fresh operational rules while preserving immutable architectural lessons.
4. **Use Native Async APIs**: When integrating memory systems into async web frameworks, always use the async client methods directly — never wrap sync calls in threads when the library internally uses asyncio.

---

## Conclusion & Resources

By coupling an SRE reasoning loop with [Hindsight](https://github.com/vectorize-io/hindsight), ChronosOps transitioned from reactive panic to deterministic, institutional problem-solving. AI agents do not need to replace engineers — they need to remember what engineers have already solved.

**Full source code**: [github.com/tahirkhan05/ChronosOps](https://github.com/tahirkhan05/ChronosOps)

- [Hindsight GitHub Repository](https://github.com/vectorize-io/hindsight)
- [Official Hindsight Documentation](https://hindsight.vectorize.io/)
- [Vectorize Agent Memory](https://vectorize.io/what-is-agent-memory)

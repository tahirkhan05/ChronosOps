# ⚡ ChronosOps — Autonomous SRE Incident Copilot & Causal Memory Nexus

> **Eliminating repeat cloud outages with persistent institutional memory powered by [Vectorize Hindsight](https://github.com/vectorize-io/hindsight)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Hindsight Memory](https://img.shields.io/badge/Memory_Engine-Vectorize_Hindsight-8b5cf6.svg)](https://hindsight.vectorize.io/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg)](https://python.org)
[![Built for HackwithHyderabad 3.0](https://img.shields.io/badge/HackwithHyderabad_3.0-Submission-ff6b35.svg)](#)

---

## 🌟 What is ChronosOps?

When production dies at 3 AM, **stateless AI agents are dangerous.**

Standard LLMs recommend generic textbook fixes — `kubectl rollout restart`, flush the Redis cache, bump max_connections — that treat symptoms without knowing the systemic constraints your engineering team learned the hard way six weeks ago.

**ChronosOps** solves this by embedding **Vectorize Hindsight** as an autonomic institutional memory core. It:

- Retains blameless post-mortems across every resolved incident (`client.aretain`)
- Maps cross-service entity topologies (Kafka → payment-service → PgBouncer → Postgres)
- Uses **TEMPR multi-strategy recall** (Temporal · Entity Graph · Multi-strategy · Semantic · Graph) to intercept active alerts at 3 AM and surface the exact post-mortem that applies
- Enforces **negative operational constraints** — it blocks the restart that took down everything last time
- Prescribes safe, non-destructive, institutionally-validated runbooks, not generic advice

The result: incidents that used to cause 34-minute $180k outages get resolved in **4.2 minutes with zero dropped messages.**

---

## 🚀 Core Features

| Feature | Description |
|---|---|
| 🚨 **Live SRE War Room** | Real-time telemetry (P99 latency, error rate, consumer lag), live K8s log stream, animated sparkline waveform |
| 🧠 **Hindsight TEMPR Memory Tracer** | Visual TEMPR score breakdown: Semantic · Entity Graph · Keyword · Temporal, live per triage call |
| ⚡ **Time-Machine Benchmark** | 1-click side-by-side: Stateless AI failure vs Hindsight-augmented recovery across 4 SEV-1/2 scenarios |
| 🛡️ **Negative Constraint Enforcement** | Proactively blocks destructive naive actions based on retained post-mortem guardrails |
| 📝 **Post-Mortem Continuous Learning** | Synthesizes blameless post-mortems on resolution, retains them into Hindsight permanently via `aretain` |
| 🔍 **Memory Bank Inspector** | Search and browse all retained institutional incidents with full TEMPR vector metadata |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CHRONOSOPS WAR ROOM (Browser UI)           │
│      Dark Glassmorphism · Live Telemetry · Runbooks     │
└────────────────────────┬────────────────────────────────┘
                         │  REST API (FastAPI)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND CORE (Python)              │
│        Triage Engine · Benchmark Runner · Memory API   │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┴────────────┐
       ▼                        ▼
┌─────────────┐      ┌──────────────────────────────────┐
│  LLM LAYER  │      │     HINDSIGHT MEMORY ENGINE       │
│  (Gemini /  │      │   Bank: chronosops-sre-nexus      │
│  Groq / OAI)│      │   arecall · aretain (native async)│
└─────────────┘      └────────────┬─────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
         [Temporal]        [Entity Graph]      [Causal Rules]
         Decay-weighted    Service topology    Negative constraints
         precedent recall  hop resolution      & safety guardrails
```

---

## 🕹️ Production Outage Scenarios

| Scenario | Stateless AI (No Memory) | Consequence | ChronosOps + Hindsight | Outcome |
|---|---|---|---|---|
| **SEV-1: Kafka Rebalance Storm** · `payment-service` | `kubectl rollout restart` | 💥 45-min cascade, DB locks, $180k | Drain partitions → patch JVM timeouts → coordinated restart | ✅ 4.2 min, 0 dropped msgs |
| **SEV-1: Vault Token Cascade** · `auth-gateway` | Flush Redis + delete pods | 💥 Global cold-cache token stampede | Jitter backoff → extend lease TTL → warm cache | ✅ 90 sec, sessions intact |
| **SEV-2: PgBouncer Saturation** · `checkout-service` | Bump max_connections + restart DB | 💥 10-min DB downtime at peak | Kill rogue analytics PID → switch pool mode | ✅ 15 sec, zero restarts |
| **SEV-1: gRPC Socket Exhaustion** · `billing-api` | Blame Stripe API + scale pods | 💥 Burns node ports, 3h lost billing | Singleton channel patch → sysctl `tcp_tw_reuse` | ✅ 60 sec, egress restored |

---

## 🛠️ Quickstart

### 1. Clone
```bash
git clone https://github.com/tahirkhan05/ChronosOps.git
cd ChronosOps
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys (Optional)
```bash
cp .env.example .env
# Edit .env with your keys — both are optional, ChronosOps runs fully offline too
```

| Key | Where to get | Required? |
|---|---|---|
| `HINDSIGHT_API_KEY` | [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io) | Optional (embedded TEMPR engine works without it) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Optional (deterministic SRE engine works without it) |

### 4. Launch
```bash
python run.py
```

Open **[http://localhost:8000](http://localhost:8000)** — the War Room is live. 🟢

---

## 💡 How Hindsight Memory Works Here

ChronosOps uses **three** Hindsight operations in production:

### `client.aretain` — Ingesting Post-Mortems
When an incident resolves, the Post-Mortem Studio calls:
```python
await client.aretain(
    bank_id="chronosops-sre-nexus",
    content="""INC-8821 Post-Mortem: Root Cause: Pod restarts in payment-service
    triggered Kafka consumer rebalance storm on 'order-tx-events'.
    CRITICAL RULE: Never restart without draining partitions first via
    /opt/sre/drain-kafka.sh and setting session.timeout.ms=45000.""",
    tags=["incident", "kafka", "payment", "sev1", "postmortem"]
)
```

### `client.arecall` — Querying During Live Incidents
When a new alert fires, the triage engine runs a TEMPR query:
```python
recalled = await client.arecall(
    bank_id="chronosops-sre-nexus",
    query="payment-service 504 timeout Kafka consumer lag pod restart",
    max_tokens=2048,
    budget="high"
)
# Returns INC-8821 with 98% entity graph match → blocks naive restart
```

### Local TEMPR Fallback Engine
If the bank is new or offline, ChronosOps uses a built-in TEMPR scoring engine with 4 pre-seeded institutional incident post-mortems — ensuring zero-config, instant demonstrations.

---

## 📁 Repository Structure

```
ChronosOps/
├── backend/
│   ├── app.py                   # FastAPI server & async API endpoints
│   ├── hindsight_manager.py     # Async Hindsight client (arecall/aretain) + TEMPR engine
│   ├── incident_scenarios.py    # 4 high-stakes enterprise outage scenarios
│   └── llm_client.py            # Multi-provider LLM reasoning (Gemini/Groq/OpenAI/local)
├── frontend/
│   ├── index.html               # Cyberpunk SRE War Room — 4-tab SPA
│   ├── style.css                # Dark glassmorphism, neon telemetry, micro-animations
│   └── app.js                   # Live triage, TEMPR gauges, benchmark, memory bank
├── deliverables/
│   ├── article.md               # ~1,500 word engineering article (dev.to / Hashnode ready)
│   ├── pitch_deck.md            # Hackathon judge evaluation guide (all 5 scoring criteria)
│   ├── video_script.md          # 3-minute demo walkthrough with YouTube title ideas
│   ├── thumbnail_prompt.md      # Viral YouTube thumbnail image prompt
│   └── social_post.txt          # Twitter & LinkedIn post copy
├── requirements.txt
├── .env.example
└── run.py                       # One-command startup
```

---

## 🔑 Key Technical Decisions

1. **Native async `arecall`/`aretain`** — The `hindsight_client` uses `asyncio.wait_for` internally. We call the native async methods directly from FastAPI's async endpoints (no thread pool hacks), eliminating the `Timeout context manager should be used inside a task` conflict entirely.

2. **TEMPR + Cloud Merge** — Local TEMPR scoring runs first for speed, then cloud `arecall` results are merged and deduplicated. If the cloud bank is empty, the system falls back gracefully to 4 pre-seeded institutional post-mortems.

3. **Negative Constraints as First-Class Citizens** — The danger banner is not decorative. It is populated from the `danger_warning` field generated by the LLM after reading recalled memories, specifically designed to surface "don't do X" rules.

---

## 🔗 Resources

- **Hindsight GitHub**: [github.com/vectorize-io/hindsight](https://github.com/vectorize-io/hindsight)
- **Hindsight Documentation**: [hindsight.vectorize.io](https://hindsight.vectorize.io/)
- **Vectorize Agent Memory**: [vectorize.io/what-is-agent-memory](https://vectorize.io/what-is-agent-memory)
- **HackwithHyderabad 3.0**: Built for the Hindsight Track

---

## 📄 License

MIT — go build something that remembers.

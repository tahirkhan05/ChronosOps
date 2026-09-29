# ChronosOps: Autonomous SRE Incident Copilot & Causal Memory Nexus
### Hackathon Pitch & Judge Evaluation Guide — HackwithHyderabad 3.0

---

## 1. Innovation (Weight: 30%)

**The problem no one else is solving at this hackathon:**

Every AI SRE tool at every hackathon does the same thing — ingest logs, query a RAG database, ask GPT-4 what to do. ChronosOps is built around a fundamentally different insight: **in distributed infrastructure, knowing what NOT to do is more critical than knowing what to do.**

- **Negative Constraint Memory**: ChronosOps is the first incident copilot specifically designed to retain and enforce institutional "don'ts" — operational guardrails learned from past post-mortems. Standard AI has no concept of "we tried this six weeks ago and it caused a 34-minute cascade."
- **Causal Entity Graph Recall**: Rather than naive keyword similarity, the TEMPR engine traces causal topology — `pod restart` → `Kafka partition reassignment` → `max.poll.interval.ms exceeded` → `DB connection cascade` — the exact failure chain that human engineers understand but stateless AI always misses.
- **Target Domain**: Tier-0 cloud outages cost $300,000/hour in enterprise. This is not a student tutor or quiz app — it targets the highest-stakes, highest-cost workflow in production engineering.

---

## 2. Use of Hindsight Memory (Weight: 25%)

**Memory is the entire product, not a feature:**

ChronosOps cannot function safely without Hindsight. A stateless model produces advice (`kubectl rollout restart`) that actively causes catastrophic cascading failures.

### The Learning Progression:
| Phase | What Happens | Hindsight Operation |
|---|---|---|
| **Day 1 — Cold Start** | Alert fires. Agent observes symptoms, runs generic triage. No memory of past events. | — |
| **Day 1 — Resolution** | Incident resolved in 34 min by human SRE. Blameless post-mortem written. | `await client.aretain(bank_id="chronosops-sre-nexus", content=postmortem, tags=[...])` |
| **Day 45 — Repeat Alert** | Same failure signature appears. Agent instantly recalls `INC-8821`. | `await client.arecall(bank_id="chronosops-sre-nexus", query=active_telemetry, budget="high")` |
| **Day 45 — Safe Resolution** | Blocks naive restart. Runs drain script. Resolves in 4.2 minutes. | TEMPR scores surface: Semantic 96%, Entity Graph 99%, Temporal 91% |

### Why `arecall` over naive RAG:
Standard RAG finds text similarity. Hindsight's TEMPR recall finds **causal relationship similarity** — it understands that `billing-api timeout` and `gRPC ManagedChannel leak` are related through shared infrastructure topology, not just word overlap.

### Native Async Integration:
ChronosOps uses `arecall` and `aretain` (the native async Hindsight methods) directly from FastAPI's async endpoints — zero event-loop conflicts, zero thread pool hacks. This is the architecturally correct production integration pattern.

---

## 3. Technical Implementation (Weight: 20%)

- **FastAPI + Native Async Hindsight**: All memory operations use `await client.arecall()` and `await client.aretain()` — properly integrated with FastAPI's async event loop, no sync wrapper conflicts.
- **Dual-Engine Resilience**: If the Hindsight Cloud bank is new or empty, a built-in TEMPR scoring engine (lexical overlap + entity graph + temporal decay) ensures instant, zero-config demonstrations with 4 pre-seeded production post-mortems.
- **Multi-Provider LLM**: Pluggable support for Gemini (primary), Groq (ultra-fast), OpenAI, and a deterministic SRE reasoning engine fallback.
- **4 Enterprise Outage Scenarios**: Kafka rebalance storm, Vault token cascade, PgBouncer saturation, gRPC socket exhaustion — each with realistic telemetry, K8s log streams, TEMPR recall, and safe runbook prescriptions.
- **Live Execution Simulator**: The runbook terminal executes step-by-step non-destructive remediation in real-time and visually normalizes the P99 latency sparkline upon recovery.

---

## 4. User Experience & Aesthetics (Weight: 15%)

- **Cyberpunk SRE War Room**: Dark glassmorphism UI with neon cyan/emerald/purple accents, animated P99 latency waveform canvas, live K8s log stream, and pulsing status indicators.
- **TEMPR Score Dials**: Animated progress gauges showing Semantic, Entity Graph, Keyword, and Temporal recall scores per triage call — making the invisible (memory retrieval) visible.
- **Time-Machine Benchmark**: Interactive 1-click side-by-side that proves the value proposition in 10 seconds — the clearest possible hackathon demo moment.
- **Web Audio Feedback**: Subtle tactile audio synthesis (Web Audio API) on every button interaction — the UI feels alive and responsive.
- **Toast Notifications + Runbook Console**: Real-time execution feedback with animated progress bar and sparkline recovery animation upon successful remediation.

---

## 5. Real-World Impact (Weight: 10%)

- **Tribal Knowledge Loss is Eliminated**: SRE on-call rotations, engineer turnover, and 3 AM cognitive load constantly cause repeat outages. ChronosOps makes institutional memory queryable, permanent, and enforced at runtime.
- **Direct Revenue Protection**: Based on published cloud downtime cost benchmarks ($300k/hour for Tier-0), preventing even one 34-minute outage per month delivers ~$170,000 in monthly value per engineering team.
- **Zero Architecture Disruption**: Plugs into existing Prometheus/OpenTelemetry/Kubernetes webhook pipelines. No agents to install, no infrastructure changes — just a memory layer on top of existing alerting.
- **Scales with the Team**: Every resolved incident makes the system smarter. Day 1 is useful; Day 365 is indispensable.

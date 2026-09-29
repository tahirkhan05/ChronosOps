"""
ChronosOps - Autonomous Enterprise SRE Incident Scenarios
Defines high-stakes, realistic production outage scenarios with scenario-specific runbooks.
"""

from typing import List, Dict, Any

INCIDENT_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "scenario_kafka_storm",
        "title": "SEV-1: Payment Gateway HTTP 504 Spike & Consumer Lag Explosion",
        "service": "payment-service",
        "severity": "SEV-1",
        "env": "production-us-east-1",
        "incident_ref": "PD-98421",
        "on_call": "Dave Miller (Staff SRE)",
        "symptoms": [
            "P99 latency jumped from 45ms to 8,200ms in payment-service",
            "HTTP 504 Gateway Timeouts at 18.4% error rate across checkout flow",
            "Kafka lag on topic 'order-tx-events' accumulating at 14,000 msgs/sec",
            "Postgres active connection pool hitting 98% saturation"
        ],
        "telemetry": {
            "error_rate": "18.4%",
            "p99_latency": "8,200ms",
            "cpu_util": "94.2%",
            "kafka_lag": "142,500 msgs",
            "db_conns": "196 / 200",
            "qps": "4,210 req/s"
        },
        "raw_logs": """[2026-09-29T14:15:02.102Z] ERROR [payment-service] org.apache.kafka.clients.consumer.CommitFailedException: Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member. This means that the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms.
[2026-09-29T14:15:04.412Z] WARN  [payment-service] io.grpc.internal.ServerCallImpl: Cancelling call due to client timeout: /payment.v1.TransactionService/AuthorizeTransaction (latency: 8210ms)
[2026-09-29T14:15:07.891Z] ERROR [ingress-nginx] 504 Gateway Time-out upstream: http://10.244.12.89:8080/v1/charge
[2026-09-29T14:15:09.110Z] ERROR [payment-service] HikariPool-1 - Connection is not available, request timed out after 30002ms.
[2026-09-29T14:15:11.305Z] WARN  [payment-service] Marking partition order-tx-events-12 as DEAD due to heartbeat loss.""",
        "target_memory_id": "mem_001_kafka_storm",
        "runbook_steps": [
            "Initializing automated remediation pipeline for payment-service...",
            "Checking Hindsight memory bank for institutional negative constraints...",
            "Enforcing safety guardrail: Blocking uncoordinated pod restart...",
            "Executing safe partition drain: /opt/sre/drain-kafka.sh --topic order-tx-events --timeout 30s... [OK]",
            "Hot-patching JVM ConfigMap: setting session.timeout.ms=45000 & max.poll.interval.ms=300000... [OK]",
            "Initiating coordinated rolling restart with 30s termination grace period... [OK]",
            "Verifying consumer lag drain: Lag dropped to 0 msgs/s. Error rate 0.00%. P99 latency restored to 38ms.",
            "Incident resolved in 4.2 minutes. Zero dropped transaction offsets."
        ],
        "stateless_ai_diagnosis": {
            "approach": "Generic LLM (Without Memory)",
            "analysis": "The payment service is experiencing high CPU and database connection exhaustion. HTTP 504 errors indicate the container is overwhelmed.",
            "recommended_action": "kubectl rollout restart deployment/payment-service && kubectl scale deployment/payment-service --replicas=25",
            "consequence": "DISASTER: Rolling restart without draining Kafka partitions triggers immediate consumer rebalance storm across all 25 pods. Database locks multiply by 3x. Total outage duration extends to 45 minutes with $180,000 lost revenue.",
            "failure_reason": "Stateless LLM has no memory that Kafka consumer group rebalances lock partition offsets during active DB transactions."
        },
        "hindsight_ai_diagnosis": {
            "approach": "ChronosOps (With Hindsight Memory)",
            "recalled_memory_id": "mem_001_kafka_storm",
            "recalled_incident": "INC-8821: Kafka Consumer Group Rebalance Storm & Silent Partition Starvation (45 days ago)",
            "analysis": "Hindsight recalled INC-8821 (Staff SRE Dave Miller post-mortem). This is NOT standard CPU exhaustion; it is an active partition rebalance cascade triggered by consumer heartbeat starvation while waiting on slow DB locks.",
            "recommended_action": "/opt/sre/drain-kafka.sh --topic order-tx-events && kubectl patch configmap payment-config -p '{\"data\":{\"session.timeout.ms\":\"45000\"}}'",
            "consequence": "SAVED: Incident resolved in 4.2 minutes with zero dropped transaction offsets and zero database deadlock spikes.",
            "advantage": "Hindsight prevented catastrophic naive pod restart by retrieving institutional post-mortem."
        }
    },
    {
        "id": "scenario_vault_cascade",
        "title": "SEV-1: Cross-Region Auth Gateway 504s & Vault Rate-Limit 429",
        "service": "auth-gateway",
        "severity": "SEV-1",
        "env": "production-us-east-1 / us-west-2",
        "incident_ref": "PD-98422",
        "on_call": "Elena Rostova (Principal SRE)",
        "symptoms": [
            "All login requests returning HTTP 504 across web and mobile",
            "Vault cluster reporting 429 Too Many Requests on `/v1/auth/token/renew-self`",
            "Redis auth cache hit-ratio dropped from 99.4% to 12.1%",
            "450 worker threads blocked on TLS handshake to Vault agent"
        ],
        "telemetry": {
            "error_rate": "24.1%",
            "p99_latency": "11,400ms",
            "cpu_util": "42.0%",
            "vault_qps": "18,900 req/s",
            "active_threads": "450 / 450",
            "qps": "12,800 req/s"
        },
        "raw_logs": """[2026-09-29T16:02:11.002Z] ERROR [auth-gateway] VaultClientException: Error renewing token: [HTTP 429] rate limit exceeded on path /v1/auth/token/renew-self
[2026-09-29T16:02:12.331Z] ERROR [auth-gateway] TokenRenewalWorker: Thread-284 failed to refresh token lease within 500ms timeout
[2026-09-29T16:02:14.992Z] WARN  [redis-cluster] Evicting key auth:session:jwt_user_89882 due to memory pressure or TTL expiration
[2026-09-29T16:02:16.115Z] ERROR [auth-gateway] Failed to validate bearer token: upstream Vault unavailable. Returning 504.""",
        "target_memory_id": "mem_002_vault_eviction",
        "runbook_steps": [
            "Initializing automated remediation pipeline for auth-gateway...",
            "Querying Hindsight memory bank for Vault rate-limit precedents...",
            "Enforcing safety guardrail: Preventing Redis cache flush & cold-cache container restart...",
            "Applying dynamic quota burst: vault write sys/quotas/rate-limit/auth-renew rate=12000 burst=25000... [OK]",
            "Executing lease TTL extension: python3 /opt/sre/extend-vault-leases.py --lease-ttl 72h... [OK]",
            "Injecting jitter backoff configuration in /etc/vault-agent/config.hcl... [OK]",
            "Warming Redis session token cache gradually... [OK]",
            "Vault QPS stabilized at 1,200 req/s. Login latency dropped to 42ms. Zero dropped sessions."
        ],
        "stateless_ai_diagnosis": {
            "approach": "Generic LLM (Without Memory)",
            "analysis": "Auth gateway is failing with HTTP 504 because Vault is rate-limiting requests. Redis cache has dropped.",
            "recommended_action": "kubectl delete pod -l app=auth-gateway && redis-cli flushdb",
            "consequence": "DISASTER: Restarting auth-gateway with cleared Redis cache creates an immediate 'cold cache token stampede'. 10,000 active clients hammer Vault simultaneously, knocking down the central Vault primary cluster completely.",
            "failure_reason": "Stateless AI doesn't know that cold cache restart turns a localized rate-limit into a global authentication black-hole."
        },
        "hindsight_ai_diagnosis": {
            "approach": "ChronosOps (With Hindsight Memory)",
            "recalled_memory_id": "mem_002_vault_eviction",
            "recalled_incident": "INC-8904: Cross-Region Vault Token TTL Eviction & Auth Gateway Cascade (32 days ago)",
            "analysis": "Hindsight recalled INC-8904 (Principal SRE Elena post-mortem). The rate limit is caused by missing exponential backoff jitter in the token renewal daemon during network blips.",
            "recommended_action": "vault write sys/quotas/rate-limit/auth-renew rate=12000 burst=25000 && /opt/sre/extend-vault-leases.py --lease-ttl 72h",
            "consequence": "SAVED: Vault QPS drops from 18,900 to 1,200 req/sec within 90 seconds. All logins restored without dropping a single active user session.",
            "advantage": "Hindsight recalled critical negative constraint: cold-cache restarts cause catastrophic stampedes."
        }
    },
    {
        "id": "scenario_pg_saturation",
        "title": "SEV-2: Checkout Latency & PgBouncer Connection Starvation",
        "service": "checkout-service",
        "severity": "SEV-2",
        "env": "production-eu-west-1",
        "incident_ref": "PD-98423",
        "on_call": "Alex Chen (Lead DBA)",
        "symptoms": [
            "Checkout API response time climbing from 45ms to 12,500ms",
            "PgBouncer client pool exhausted (200/200 active connections)",
            "Unindexed query lock detected on `customer_ledgers` table",
            "Deadlock alerts triggering on Postgres replica node 3"
        ],
        "telemetry": {
            "error_rate": "8.7%",
            "p99_latency": "12,500ms",
            "db_conns": "200 / 200",
            "pgbouncer_wait": "412 clients",
            "cpu_util": "88.5%",
            "qps": "2,150 req/s"
        },
        "raw_logs": """[2026-09-29T18:30:01.401Z] ERROR [checkout-service] org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved for non-replication superuser connections
[2026-09-29T18:30:03.119Z] WARN  [pgbouncer] client_login_timeout: closing client [10.244.18.22:48902] waiting in queue for 15000ms
[2026-09-29T18:30:06.912Z] LOG   [postgres] process 42891 still waiting for ExclusiveLock on relation 18920 'customer_ledgers' after 1000.123 ms""",
        "target_memory_id": "mem_003_pg_pool_saturation",
        "runbook_steps": [
            "Initializing automated remediation pipeline for checkout-service...",
            "Querying Hindsight memory bank for database connection starvation precedents...",
            "Enforcing safety guardrail: Blocking dangerous primary database restart...",
            "Executing query kill: SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%customer_ledgers%' AND pid > 40000;... [OK]",
            "Hot-reloading PgBouncer configuration: switching pool_mode = transaction... [OK]",
            "Enforcing statement timeout: ALTER DATABASE checkout SET statement_timeout = '3000ms';... [OK]",
            "Verifying client queue: PgBouncer waiting clients dropped to 0. Latency normalized to 28ms."
        ],
        "stateless_ai_diagnosis": {
            "approach": "Generic LLM (Without Memory)",
            "analysis": "Postgres connection pool is full. Checkout service cannot obtain database connections.",
            "recommended_action": "sed -i 's/max_connections = 200/max_connections = 800/' /etc/postgresql.conf && systemctl restart postgresql",
            "consequence": "SEVERE DEGRADATION: Bumping max_connections directly on Postgres primary causes memory thrashing, CPU context-switch storm, and requires 10 minutes of DB restart downtime during peak sales window.",
            "failure_reason": "Stateless AI misses that the bottleneck is connection pooling mode and a rogue analytics transaction."
        },
        "hindsight_ai_diagnosis": {
            "approach": "ChronosOps (With Hindsight Memory)",
            "recalled_memory_id": "mem_003_pg_pool_saturation",
            "recalled_incident": "INC-9102: Postgres PgBouncer Connection Saturation under Spike Load (19 days ago)",
            "analysis": "Hindsight recalled INC-9102 (DBA Lead Alex post-mortem). This exact signature happens when an unindexed analytics report acquires table locks in session-pooling mode.",
            "recommended_action": "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%customer_ledgers%' AND state = 'active' AND pid != pg_backend_pid();",
            "consequence": "SAVED: Database connection wait time drops to 2ms in 15 seconds with zero database downtime.",
            "advantage": "Hindsight pinpointed the exact SQL remediation and configuration fix without touching the primary database engine."
        }
    },
    {
        "id": "scenario_grpc_leak",
        "title": "SEV-1: Ephemeral Port Exhaustion & Silent Egress Timeout in Billing API",
        "service": "billing-api",
        "severity": "SEV-1",
        "env": "production-ap-southeast-1",
        "incident_ref": "PD-98424",
        "on_call": "Marcus Vance (Senior SRE)",
        "symptoms": [
            "All outbound credit card authorization calls failing with 'i/o timeout'",
            "Pods show 'Running' and 0% CPU with green Kubernetes health probes",
            "Node netstat reveals 65,535 TCP sockets stuck in TIME_WAIT state",
            "Stripe and Adyen webhooks failing with connection refused"
        ],
        "telemetry": {
            "error_rate": "100.0% (Egress)",
            "p99_latency": "30,000ms",
            "sockets": "65,535 / 65,535",
            "pod_health": "100% HEALTHY",
            "cpu_util": "3.1%",
            "qps": "850 req/s"
        },
        "raw_logs": """[2026-09-29T19:10:04.102Z] ERROR [billing-api] TransportException: connect to gateway.stripe.com:443 failed: cannot assign requested address (errno 99)
[2026-09-29T19:10:05.419Z] WARN  [kernel] TCP: out of ephemeral ports on interface eth0 (allocating > 65530 sockets)
[2026-09-29T19:10:08.201Z] ERROR [billing-api] Payment authorization dispatch aborted: socket pool starved.""",
        "target_memory_id": "mem_004_grpc_leak",
        "runbook_steps": [
            "Initializing automated remediation pipeline for billing-api...",
            "Querying Hindsight memory bank for socket exhaustion & gRPC channel leaks...",
            "Enforcing safety guardrail: Preventing destructive pod replica scale-up...",
            "Deploying ConfigMap patch: kubectl set env deployment/billing-api BILLING_USE_SINGLETON_CHANNEL=true... [OK]",
            "Tuning kernel TCP parameter: sysctl -w net.ipv4.tcp_tw_reuse=1... [OK]",
            "Recycling TIME_WAIT socket pool on worker node network namespace... [OK]",
            "Verifying egress connectivity: Successfully authorized test transaction with gateway.stripe.com:443 (latency 44ms).",
            "Egress restored. Outbound error rate dropped to 0.00%."
        ],
        "stateless_ai_diagnosis": {
            "approach": "Generic LLM (Without Memory)",
            "analysis": "Kubernetes reports pods are healthy. Egress connection refused means Stripe or Adyen payment gateway is having an outage.",
            "recommended_action": "Wait for upstream payment gateway status page update. Scale billing-api replicas from 5 to 20.",
            "consequence": "CATASTROPHE: Blaming the payment vendor while pods remain dead causes 3 hours of lost revenue. Scaling up pods burns remaining node ports across the entire Kubernetes worker cluster.",
            "failure_reason": "Stateless AI is tricked by green health checks and misdiagnoses self-inflicted socket leaks as upstream third-party downtime."
        },
        "hindsight_ai_diagnosis": {
            "approach": "ChronosOps (With Hindsight Memory)",
            "recalled_memory_id": "mem_004_grpc_leak",
            "recalled_incident": "INC-9244: Silent gRPC Channel Leak & Ephemeral Socket Exhaustion (7 days ago)",
            "analysis": "Hindsight recalled INC-9244 (SRE Marcus post-mortem). This is a known SDK bug where non-singleton gRPC channels leak TIME_WAIT sockets under packet loss.",
            "recommended_action": "kubectl set env deployment/billing-api BILLING_USE_SINGLETON_CHANNEL=true && sysctl -w net.ipv4.tcp_tw_reuse=1",
            "consequence": "SAVED: All egress network traffic restored within 60 seconds without blaming upstream partners.",
            "advantage": "Hindsight recognized the deceptive 'healthy pod + errno 99' socket leak signature instantly."
        }
    }
]

def get_scenario_by_id(scenario_id: str) -> Dict[str, Any]:
    for s in INCIDENT_SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return INCIDENT_SCENARIOS[0]

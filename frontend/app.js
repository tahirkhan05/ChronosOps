// ChronosOps Frontend Logic - Enterprise SRE War Room

let currentScenarios = [];
let activeScenarioId = "scenario_kafka_storm";
let isTriageRunning = false;
let latencyHistory = [];
let sparklineAnimInterval = null;

document.addEventListener("DOMContentLoaded", async () => {
    initNavigation();
    initSparkline();
    await fetchSystemStatus();
    await loadScenarios();
    await loadBenchmark(activeScenarioId);
    await loadMemoryBank();
    initEventListeners();
});

// Sound feedback synthesizer (Web Audio API)
function playTactileAudio(type = "click") {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === "click") {
            osc.frequency.setValueAtTime(800, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.05);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.05);
        } else if (type === "success") {
            osc.frequency.setValueAtTime(520, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
            gain.gain.setValueAtTime(0.12, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.15);
        }
    } catch (e) {
        // Audio optional
    }
}

// Navigation Tabs
function initNavigation() {
    const tabs = document.querySelectorAll(".nav-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            playTactileAudio("click");
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const target = tab.getAttribute("data-tab");
            const panel = document.getElementById(`${target}-view`);
            if (panel) panel.classList.add("active");

            if (target === "memory-bank") loadMemoryBank();
            if (target === "benchmark") loadBenchmark(activeScenarioId);
        });
    });
}

// System Status
async function fetchSystemStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const statusEl = document.getElementById("hindsightStatusText");
        if (statusEl) statusEl.textContent = data.is_cloud_connected ? "Hindsight Cloud: Synchronized" : "Hindsight Embedded: Ready";
        const modelEl = document.getElementById("llmModelDisplay");
        if (modelEl) modelEl.textContent = data.llm_model || "gemini-3.5-flash-lite";
        const bankEl = document.getElementById("bankIdDisplay");
        if (bankEl) bankEl.textContent = data.hindsight_bank_id;
    } catch (e) {
        console.error("Status error:", e);
    }
}

// Load Scenarios
async function loadScenarios() {
    try {
        const res = await fetch("/api/scenarios");
        const data = await res.json();
        currentScenarios = data.scenarios;
        renderScenarioChips();
        renderBenchmarkPills();
        selectScenario(activeScenarioId);
    } catch (e) {
        console.error("Scenarios load error:", e);
    }
}

function renderScenarioChips() {
    const container = document.getElementById("scenarioChipsContainer");
    container.innerHTML = "";
    currentScenarios.forEach(sc => {
        const btn = document.createElement("button");
        btn.className = `scenario-chip-btn ${sc.id === activeScenarioId ? 'active' : ''}`;
        btn.textContent = `${sc.severity}: ${sc.service}`;
        btn.addEventListener("click", () => {
            playTactileAudio("click");
            selectScenario(sc.id);
        });
        container.appendChild(btn);
    });
}

function renderBenchmarkPills() {
    const container = document.getElementById("benchmarkPills");
    container.innerHTML = "";
    currentScenarios.forEach(sc => {
        const btn = document.createElement("button");
        btn.className = `bench-chip-btn ${sc.id === activeScenarioId ? 'active' : ''}`;
        btn.textContent = `${sc.severity} - ${sc.service}`;
        btn.addEventListener("click", () => {
            playTactileAudio("click");
            document.querySelectorAll(".bench-chip-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadBenchmark(sc.id);
        });
        container.appendChild(btn);
    });
}

function selectScenario(id) {
    activeScenarioId = id;
    const scenario = currentScenarios.find(s => s.id === id);
    if (!scenario) return;

    // Update chips
    document.querySelectorAll(".scenario-chip-btn").forEach((chip, i) => {
        chip.classList.toggle("active", currentScenarios[i].id === id);
    });

    // Populate War Room Details
    document.getElementById("activeIncidentTitle").textContent = scenario.title;
    document.getElementById("activeSeverityBadge").textContent = scenario.severity;
    document.getElementById("activeServiceBadge").textContent = scenario.service;
    document.getElementById("activeIncidentRef").textContent = scenario.incident_ref || "PD-98421";
    document.getElementById("activeEnvBadge").textContent = scenario.env;
    document.getElementById("onCallName").textContent = scenario.on_call || "On-Call SRE";

    // Telemetry Grid
    const teleGrid = document.getElementById("telemetryGrid");
    teleGrid.innerHTML = "";
    for (const [key, val] of Object.entries(scenario.telemetry)) {
        const box = document.createElement("div");
        box.className = "tele-box";
        box.innerHTML = `
            <div class="tele-box-title">${key.replace(/_/g, ' ')}</div>
            <div class="tele-box-num">${val}</div>
        `;
        teleGrid.appendChild(box);
    }

    // Symptoms List
    const symList = document.getElementById("activeSymptomsList");
    symList.innerHTML = "";
    scenario.symptoms.forEach(sym => {
        const li = document.createElement("li");
        li.textContent = sym;
        symList.appendChild(li);
    });

    // Terminal Logs
    document.getElementById("terminalLogs").textContent = scenario.raw_logs;

    // Reset Latency Waveform
    resetLatencyWaveform(scenario.telemetry.p99_latency);

    // Hide previous execution console
    document.getElementById("runbookConsole").style.display = "none";

    // Run triage automatically
    runTriage(scenario.id);
}

// Sparkline Canvas Rendering
function initSparkline() {
    const canvas = document.getElementById("latencyCanvas");
    if (!canvas) return;
    drawSparkline(canvas);
}

function resetLatencyWaveform(currentLatencyStr) {
    latencyHistory = [];
    const baseVal = parseInt(currentLatencyStr.replace(/[^0-9]/g, '')) || 8000;
    for (let i = 0; i < 30; i++) {
        latencyHistory.push(baseVal + (Math.random() * 800 - 400));
    }
    document.getElementById("sparkCurrentVal").textContent = `${currentLatencyStr} (Degraded)`;
    document.getElementById("sparkCurrentVal").className = "spark-current text-danger";
    drawSparkline();
}

function drawSparkline() {
    const canvas = document.getElementById("latencyCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    if (latencyHistory.length < 2) return;

    const min = Math.min(...latencyHistory) * 0.8;
    const max = Math.max(...latencyHistory) * 1.1;

    ctx.beginPath();
    ctx.strokeStyle = latencyHistory[latencyHistory.length - 1] > 200 ? "#f43f5e" : "#10b981";
    ctx.lineWidth = 2.2;

    latencyHistory.forEach((val, i) => {
        const x = (i / (latencyHistory.length - 1)) * width;
        const y = height - ((val - min) / (max - min || 1)) * (height - 10) - 5;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();

    // Fill Gradient
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, latencyHistory[latencyHistory.length - 1] > 200 ? "rgba(244, 63, 94, 0.25)" : "rgba(16, 185, 129, 0.25)");
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = grad;
    ctx.fill();
}

// Run Triage with live Button Feedback
async function runTriage(scenarioId) {
    if (isTriageRunning) return;
    isTriageRunning = true;

    const btn = document.getElementById("btnRunTriage");
    const spinner = document.getElementById("triageSpinner");
    const icon = document.getElementById("triageIconSvg");
    const text = document.getElementById("btnTriageText");
    const tracerPanel = document.getElementById("memoryTracerCard");

    // Interactive Button Loading State
    btn.classList.add("loading");
    spinner.style.display = "inline-block";
    icon.style.display = "none";
    text.textContent = "Querying Hindsight Memory Bank...";
    tracerPanel.classList.add("scanning");

    try {
        const res = await fetch("/api/triage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenario_id: scenarioId, use_memory: true })
        });
        const data = await res.json();
        renderTriageResults(data);
        playTactileAudio("success");
    } catch (e) {
        console.error("Triage error:", e);
    } finally {
        isTriageRunning = false;
        btn.classList.remove("loading");
        spinner.style.display = "none";
        icon.style.display = "inline-block";
        text.textContent = "Run ChronosOps Triage";
        tracerPanel.classList.remove("scanning");
    }
}

function renderTriageResults(data) {
    const memories = data.recalled_memories || [];
    const diag = data.diagnosis;

    if (memories.length > 0) {
        const mem = memories[0];
        document.getElementById("matchTag").textContent = "HISTORICAL POST-MORTEM PRECEDENT";
        document.getElementById("matchTime").textContent = `Retained ${mem.days_ago || 30} days ago in Hindsight`;
        document.getElementById("recalledTitle").textContent = mem.title;
        document.getElementById("recalledContent").textContent = mem.content;

        // TEMPR Gauges
        const scores = mem.tempr_scores || { semantic: 0.96, entity_graph: 0.99, keyword: 0.94, temporal: 0.91 };
        document.getElementById("scoreSemantic").style.width = `${(scores.semantic || 0.95) * 100}%`;
        document.getElementById("scoreSemanticNum").textContent = scores.semantic || 0.95;

        document.getElementById("scoreGraph").style.width = `${(scores.entity_graph || 0.98) * 100}%`;
        document.getElementById("scoreGraphNum").textContent = scores.entity_graph || 0.98;

        document.getElementById("scoreKeyword").style.width = `${(scores.keyword || 0.92) * 100}%`;
        document.getElementById("scoreKeywordNum").textContent = scores.keyword || 0.92;

        document.getElementById("scoreTemporal").style.width = `${(scores.temporal || 0.90) * 100}%`;
        document.getElementById("scoreTemporalNum").textContent = scores.temporal || 0.90;

        document.getElementById("confidenceBadge").textContent = `${diag.confidence_score || 98}% RELEVANCE`;
    }

    // Danger Warning Banner
    document.getElementById("dangerBannerText").textContent = diag.danger_warning || "HINDSIGHT SAFETY GUARD: Prevented destructive naive pod restart.";

    // Actions Checklist
    const actionsList = document.getElementById("actionsChecklist");
    actionsList.innerHTML = "";
    (diag.recommended_actions || []).forEach((action, idx) => {
        const item = document.createElement("div");
        item.className = "action-item";
        item.innerHTML = `
            <div class="action-num">${idx + 1}</div>
            <div class="action-text">${action}</div>
        `;
        actionsList.appendChild(item);
    });
}

// Execute Runbook Simulator with Scenario-Specific Steps
function executeRunbook() {
    playTactileAudio("click");
    const consoleBox = document.getElementById("runbookConsole");
    const logBody = document.getElementById("runbookLogBody");
    const statusText = document.getElementById("runbookStatus");
    const progressBar = document.getElementById("runbookProgressBar");

    consoleBox.style.display = "block";
    logBody.textContent = "";
    progressBar.style.width = "0%";

    const scenario = currentScenarios.find(s => s.id === activeScenarioId);
    const steps = scenario.runbook_steps || [
        `Initializing automated remediation pipeline for ${scenario.service}...`,
        `Enforcing non-destructive constraints retrieved from Hindsight memory...`,
        `Executing verified configuration patch... [OK]`,
        `Initiating coordinated service restart... [OK]`,
        `Telemetry verification: Error rate dropped to 0.00%. Latency restored to baseline 38ms.`,
        `Incident resolved in 4.2 minutes.`
    ];

    let currentStep = 0;
    statusText.textContent = "EXECUTING RUNBOOK...";

    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            logBody.textContent += steps[currentStep] + "\n";
            logBody.scrollTop = logBody.scrollHeight;
            currentStep++;
            const pct = Math.round((currentStep / steps.length) * 100);
            progressBar.style.width = `${pct}%`;

            if (currentStep >= steps.length) {
                clearInterval(interval);
                statusText.textContent = "COMPLETED (RECOVERED)";
                playTactileAudio("success");
                showToast("🎉 Incident Successfully Mitigated via Hindsight Runbook!");

                // Visibly normalize the sparkline latency to baseline!
                for (let j = 0; j < 8; j++) {
                    latencyHistory.push(38 + Math.random() * 8);
                }
                document.getElementById("sparkCurrentVal").textContent = "38 ms (Healthy / Restored)";
                document.getElementById("sparkCurrentVal").className = "spark-current text-emerald";
                drawSparkline();
            }
        }
    }, 400);
}

// Load Benchmark Data
async function loadBenchmark(scenarioId) {
    try {
        const res = await fetch(`/api/benchmark/${scenarioId}`);
        const data = await res.json();

        // Stateless
        document.getElementById("statelessDiagnosisText").textContent = data.stateless_ai.analysis;
        document.getElementById("statelessActionCode").textContent = data.stateless_ai.recommended_action;
        document.getElementById("statelessConsequenceText").textContent = data.stateless_ai.consequence;
        document.getElementById("statelessFailureText").textContent = data.stateless_ai.failure_reason;

        // Hindsight
        document.getElementById("hindsightRecalledPill").textContent = data.hindsight_ai.recalled_incident;
        document.getElementById("hindsightDiagnosisText").textContent = data.hindsight_ai.analysis;
        document.getElementById("hindsightActionCode").textContent = data.hindsight_ai.recommended_action;
        document.getElementById("hindsightConsequenceText").textContent = data.hindsight_ai.consequence;
        document.getElementById("hindsightAdvantageText").textContent = data.hindsight_ai.advantage;
    } catch (e) {
        console.error("Benchmark error:", e);
    }
}

// Load Memory Bank
async function loadMemoryBank() {
    try {
        const res = await fetch("/api/memories");
        const data = await res.json();
        const grid = document.getElementById("memoryUnitsGrid");
        grid.innerHTML = "";

        data.memories.forEach(mem => {
            const card = document.createElement("div");
            card.className = "memory-unit-card";
            card.innerHTML = `
                <div class="mem-unit-head">
                    <span class="mem-unit-badge">${mem.metadata?.severity || 'SEV-1'} INCIDENT</span>
                    <span class="mem-unit-date">${mem.timestamp.substring(0, 10)}</span>
                </div>
                <div class="mem-unit-title">${mem.title}</div>
                <div class="mem-unit-content">${mem.content}</div>
                <div class="mem-entities-row">
                    ${(mem.entities || []).map(e => `<span class="entity-chip-tag">${e}</span>`).join('')}
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Memory bank error:", e);
    }
}

// Retain Post-Mortem
async function handleRetainPostmortem() {
    playTactileAudio("click");
    const title = document.getElementById("pmTitleInput").value;
    const entities = document.getElementById("pmEntitiesInput").value.split(",").map(e => e.trim());
    const content = document.getElementById("pmContentInput").value;
    const feedback = document.getElementById("retainFeedback");

    if (!content) return;

    feedback.textContent = "Retaining to Hindsight Cloud...";

    try {
        const res = await fetch("/api/memories/retain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                content: `${title}\n${content}`,
                tags: ["incident", "postmortem", "sev1"],
                metadata: { severity: "SEV-1", source: "Post-Mortem Studio" }
            })
        });
        const data = await res.json();
        feedback.textContent = "Successfully Retained into Hindsight Bank!";
        playTactileAudio("success");
        showToast("New Institutional Memory Unit Retained in Hindsight!");
        await fetchSystemStatus();
        await loadMemoryBank();
    } catch (e) {
        feedback.textContent = "Error retaining memory.";
        console.error(e);
    }
}

// Search Memory
async function handleSearchMemory() {
    playTactileAudio("click");
    const query = document.getElementById("memorySearchInput").value;
    if (!query) {
        loadMemoryBank();
        return;
    }

    try {
        const res = await fetch("/api/memories/recall", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, limit: 4 })
        });
        const data = await res.json();
        const grid = document.getElementById("memoryUnitsGrid");
        grid.innerHTML = "";

        if (data.results.length === 0) {
            grid.innerHTML = "<div style='color:var(--text-muted); padding:16px;'>No matching memories found for this query.</div>";
            return;
        }

        data.results.forEach(mem => {
            const card = document.createElement("div");
            card.className = "memory-unit-card";
            card.innerHTML = `
                <div class="mem-unit-head">
                    <span class="mem-unit-badge">TEMPR MATCH (${Math.round((mem.tempr_scores?.composite || 0.9) * 100)}%)</span>
                    <span class="mem-unit-date">${mem.timestamp.substring(0, 10)}</span>
                </div>
                <div class="mem-unit-title">${mem.title}</div>
                <div class="mem-unit-content">${mem.content}</div>
                <div class="mem-entities-row">
                    ${(mem.entities || []).map(e => `<span class="entity-chip-tag">${e}</span>`).join('')}
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Search error:", e);
    }
}

function showToast(msg) {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = "toast-item";
    toast.innerHTML = `<span>⚡</span> <span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

function initEventListeners() {
    document.getElementById("btnRunTriage").addEventListener("click", () => {
        playTactileAudio("click");
        runTriage(activeScenarioId);
    });
    document.getElementById("btnExecuteRemediation").addEventListener("click", executeRunbook);
    document.getElementById("btnGeneratePostmortem").addEventListener("click", () => {
        playTactileAudio("click");
        document.getElementById("tabPostmortem").click();
    });
    document.getElementById("btnRetainPostmortem").addEventListener("click", handleRetainPostmortem);
    document.getElementById("btnSearchMemory").addEventListener("click", handleSearchMemory);
    document.getElementById("memorySearchInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSearchMemory();
    });
}

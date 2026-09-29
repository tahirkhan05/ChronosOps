"""
ChronosOps - Autonomous Enterprise SRE Incident Copilot & Causal Memory Core
Main FastAPI Application Server
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.hindsight_manager import memory_manager
from backend.incident_scenarios import INCIDENT_SCENARIOS, get_scenario_by_id
from backend.llm_client import llm_client

app = FastAPI(
    title="ChronosOps - SRE Memory Nexus",
    description="Autonomous Enterprise SRE Incident Copilot Powered by Vectorize Hindsight",
    version="1.0.0"
)

# Enable CORS for flexible development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class RetainRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

class RecallRequest(BaseModel):
    query: str
    limit: Optional[int] = 4

class TriageRequest(BaseModel):
    scenario_id: Optional[str] = None
    service_name: Optional[str] = None
    symptoms: Optional[List[str]] = None
    raw_logs: Optional[str] = None
    use_memory: bool = True

# API Routes
@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "app_name": "ChronosOps",
        "hindsight_bank_id": memory_manager.bank_id,
        "is_cloud_connected": memory_manager.is_cloud_connected,
        "mode": "Hindsight Cloud Engine" if memory_manager.is_cloud_connected else "Hindsight Embedded TEMPR Core",
        "active_memories_count": len(memory_manager.list_all_memories()),
        "llm_model": llm_client.gemini_model if llm_client.gemini_api_key else "Deterministic SRE Engine"
    }

@app.get("/api/scenarios")
async def list_scenarios():
    return {"scenarios": INCIDENT_SCENARIOS}

@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    scenario = get_scenario_by_id(scenario_id)
    return {"scenario": scenario}

@app.post("/api/triage")
async def triage_incident(req: TriageRequest):
    scenario = None
    if req.scenario_id:
        scenario = get_scenario_by_id(req.scenario_id)
        service = scenario["service"]
        symptoms = scenario["symptoms"]
        logs = scenario["raw_logs"]
        title = scenario["title"]
    else:
        service = req.service_name or "unknown-service"
        symptoms = req.symptoms or ["Unspecified anomaly detected"]
        logs = req.raw_logs or ""
        title = f"Alert in {service}"

    recalled_memories = []
    if req.use_memory:
        query_text = f"{service} {' '.join(symptoms)} {logs[:300]}"
        recalled_memories = await memory_manager.recall_incident_context(query_text, limit=3, target_service=service)

    diagnosis = llm_client.generate_incident_diagnosis(
        incident_title=title,
        service=service,
        symptoms=symptoms,
        logs=logs,
        recalled_memories=recalled_memories
    )

    return {
        "incident_title": title,
        "service": service,
        "use_memory": req.use_memory,
        "recalled_memories": recalled_memories,
        "diagnosis": diagnosis,
        "scenario": scenario
    }

@app.get("/api/benchmark/{scenario_id}")
async def get_benchmark(scenario_id: str):
    scenario = get_scenario_by_id(scenario_id)
    return {
        "scenario_id": scenario_id,
        "scenario_title": scenario["title"],
        "service": scenario["service"],
        "severity": scenario["severity"],
        "telemetry": scenario["telemetry"],
        "stateless_ai": scenario["stateless_ai_diagnosis"],
        "hindsight_ai": scenario["hindsight_ai_diagnosis"]
    }

@app.get("/api/memories")
async def get_memories():
    memories = memory_manager.list_all_memories()
    return {
        "total_memories": len(memories),
        "bank_id": memory_manager.bank_id,
        "is_cloud_connected": memory_manager.is_cloud_connected,
        "memories": memories
    }

@app.post("/api/memories/recall")
async def recall_memories(req: RecallRequest):
    results = await memory_manager.recall_incident_context(req.query, limit=req.limit or 4)
    return {
        "query": req.query,
        "total_matches": len(results),
        "results": results
    }

@app.post("/api/memories/retain")
async def retain_memory(req: RetainRequest):
    if not req.content or len(req.content.strip()) < 5:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    
    res = await memory_manager.retain_incident(
        content=req.content,
        metadata=req.metadata,
        tags=req.tags
    )
    return res

# Static frontend files mounting
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True, ws="none", http="h11")

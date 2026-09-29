"""
ChronosOps - Startup Launcher
Runs FastAPI backend and serves the frontend at http://127.0.0.1:8000
"""

import sys
import uvicorn
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

if __name__ == "__main__":
    print("=" * 60)
    print("Starting ChronosOps - SRE Memory Nexus")
    print("Powered by Vectorize Hindsight Cloud & Gemini 3.5 Flash Lite")
    print("Access War Room UI at: http://127.0.0.1:8000")
    print("=" * 60)
    
    uvicorn.run(
        "backend.app:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=False,
        ws="none",
        http="h11"
    )

import os
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Initialize logger
logger = logging.getLogger("ResearchPilot.API")

# Try importing the supervisor. Make sure PYTHONPATH includes the backend folder.
try:
    from agents.supervisor import supervisor
except ImportError as e:
    logger.error(f"Import error during startup: {str(e)}")
    raise e

app = FastAPI(title="ResearchPilot Backend")

# Setup CORS middleware
# Allow Vercel frontend or * if not specified
allowed_origins = [os.getenv("ALLOWED_ORIGIN", "*")]
if "*" not in allowed_origins and os.getenv("ALLOWED_ORIGIN"):
    # Also add standard local dev server origins for testing
    allowed_origins.extend(["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:8000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-research")
async def run_research(body: QueryRequest):
    logger.info(f"Received research query request: '{body.query}'")
    
    async def event_stream():
        try:
            async for event in supervisor.run(body.query):
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Error during streaming execution: {str(e)}", exc_info=True)
            yield json.dumps({"type": "error", "agent": "supervisor", "message": str(e)}) + "\n"
            
    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    # Run server locally when main.py is executed directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

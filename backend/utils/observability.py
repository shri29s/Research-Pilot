import os
import json
import time
import logging
import datetime
from typing import Dict, Any, List

logger = logging.getLogger("ResearchPilot.Observability")

class Tracer:
    """Class to manage execution telemetry, tracing, and metric collection for ResearchPilot."""
    
    def __init__(self, query: str):
        self.query = query
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.logs_dir = "logs"
        self.trace_file = os.path.join(self.logs_dir, f"session_{self.timestamp}.jsonl")
        
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Metrics storage
        self.metrics: Dict[str, Any] = {
            "total_papers_retrieved": 0,
            "total_api_calls": 0,
            "synthesis_iterations": {},
            "critic_scores": {},
            "total_latency_ms": 0.0
        }
        
        self.steps: List[Dict[str, Any]] = []
        logger.info(f"Initialized tracer for session {self.timestamp} with query: '{query}'")

    def trace_step(self, agent_name: str, input_data: Any, output_data: Any, duration_ms: float):
        """Logs a single step in the multi-agent graph with structured details."""
        step = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": agent_name,
            "input": self._sanitize_data(input_data),
            "output": self._sanitize_data(output_data),
            "duration_ms": round(duration_ms, 2)
        }
        
        self.steps.append(step)
        
        # Write to JSONL log file
        try:
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(step) + "\n")
        except Exception as e:
            logger.error(f"Failed to write trace step to log file: {str(e)}")
            
        logger.debug(f"Traced step for {agent_name} in {duration_ms:.2f}ms")

    def increment_metric(self, name: str, value: int = 1):
        """Increments a numerical session metric."""
        if name in self.metrics:
            self.metrics[name] += value
        else:
            self.metrics[name] = value

    def set_sub_metric(self, category: str, sub_key: str, value: Any):
        """Sets a sub-metric under a specific metric category."""
        if category not in self.metrics:
            self.metrics[category] = {}
        self.metrics[category][sub_key] = value

    def finalize(self) -> Dict[str, Any]:
        """Finalizes the trace session and computes overall latency."""
        self.metrics["total_latency_ms"] = round((time.time() - self.start_time) * 1000, 2)
        
        summary = {
            "query": self.query,
            "session_id": self.timestamp,
            "metrics": self.metrics,
            "total_steps": len(self.steps)
        }
        
        # Write final session summary to trace file
        try:
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"session_summary": summary}) + "\n")
        except Exception as e:
            logger.error(f"Failed to write final session summary to log file: {str(e)}")
            
        logger.info(f"Finalized session {self.timestamp}. Latency: {self.metrics['total_latency_ms']}ms. Steps: {len(self.steps)}")
        return summary

    def _sanitize_data(self, data: Any) -> Any:
        """Helper to recursively sanitize agent inputs/outputs for JSON serialization."""
        if hasattr(data, "model_dump"):  # Pydantic v2
            return data.model_dump()
        elif hasattr(data, "dict"):  # Pydantic v1
            return data.dict()
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif hasattr(data, "__dict__"):
            return self._sanitize_data(data.__dict__)
        else:
            return str(data)

def setup_logger(log_level: str = "INFO"):
    """Configures the unified console logger for ResearchPilot."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    # Silence third-party logs
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

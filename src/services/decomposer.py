import json
import logging
from typing import List
from src.utils.llm import load_prompt, call_aimlabs

logger = logging.getLogger("ResearchPilot.DecomposerAgent")

class DecomposerAgent:
    """Agent responsible for breaking a research query into targeted sub-questions."""
    
    def __init__(self):
        self.system_instruction = load_prompt("decomposer")
        
    def run(self, query: str) -> List[str]:
        """
        Decomposes the query into sub-questions.
        Returns a list of sub-questions.
        """
        logger.info(f"Decomposing query: '{query}'")
        try:
            response_text = call_aimlabs(
                system_instruction=self.system_instruction,
                prompt=f"Research Query: {query}",
                json_mode=True
            )
            
            parsed = json.loads(response_text)
            # Handle both direct list and dict formats
            if isinstance(parsed, list):
                sub_questions = parsed
            elif isinstance(parsed, dict):
                # Look for a key containing "question" (case-insensitive)
                key = next((k for k in parsed.keys() if "question" in k.lower()), None)
                if key and isinstance(parsed[key], list):
                    sub_questions = parsed[key]
                else:
                    logger.warning(f"Decomposer returned unexpected dictionary keys: {list(parsed.keys())}. Falling back.")
                    raise ValueError("Unexpected JSON structure")
            else:
                logger.warning(f"Decomposer returned unexpected format: {response_text}. Falling back.")
                raise ValueError("Unexpected JSON structure")
            
            logger.info(f"Decomposed query into {len(sub_questions)} sub-questions: {sub_questions}")
            return [str(q).strip() for q in sub_questions if str(q).strip()]
        except Exception as e:
            logger.error(f"Error parsing decomposer response: {str(e)}")
            
        # Fallback in case LLM call or JSON parsing fails
        fallback_questions = [
            f"What are the core concepts and background of {query}?",
            f"What are the main methodologies and techniques used in relation to {query}?",
            f"What are the limitations, open challenges, and future directions for {query}?"
        ]
        logger.info(f"Using fallback sub-questions: {fallback_questions}")
        return fallback_questions

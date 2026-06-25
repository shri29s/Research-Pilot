import time
import os
import logging
from openai import OpenAI
from config import config

logger = logging.getLogger("ResearchPilot.LLM")

# Initialize OpenAI client pointing to AIMALabs
client = OpenAI(
    api_key=config.aimlabs_api_key,
    base_url=config.aimlabs_base_url
)

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt template from the prompts/ folder."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompt_path = os.path.join(base_dir, "prompts", f"{prompt_name}.txt")
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to load prompt from {prompt_path}: {str(e)}")
        raise e

def call_aimlabs(system_instruction: str, prompt: str, json_mode: bool = False) -> str:
    """
    Calls the AIMALabs API (OpenAI-compatible) with system instructions and a user prompt.
    Supports strict JSON output mode.
    Implements retries with exponential backoff on 429/quota limits.
    """
    max_retries = 5
    initial_delay = 5  # seconds
    backoff_factor = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
            
            kwargs = {
                "model": config.chat_model,
                "messages": messages,
                "temperature": 0.1
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            logger.debug(f"Calling AIMALabs (attempt {attempt}) with model {config.chat_model}")
            response = client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate_limit" in err_str.lower()
            if is_rate_limit and attempt < max_retries:
                sleep_time = initial_delay * (backoff_factor ** (attempt - 1))
                logger.warning(
                    f"AIMALabs API rate limit hit (429/quota). "
                    f"Retrying attempt {attempt}/{max_retries} in {sleep_time}s... Error: {err_str}"
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"Error calling AIMALabs on attempt {attempt}: {err_str}")
                raise e

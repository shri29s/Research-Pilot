import time
import os
import logging
from openai import OpenAI, AsyncOpenAI
from config import config

logger = logging.getLogger("ResearchPilot.LLM")

# Initialize OpenAI client pointing to AIMALabs
client = OpenAI(
    api_key=config.aimlabs_api_key,
    base_url=config.aimlabs_base_url
)

# Initialize AsyncOpenAI client pointing to AIMALabs
async_client = AsyncOpenAI(
    api_key=config.aimlabs_api_key,
    base_url=config.aimlabs_base_url
)

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt template from the prompts/ folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Compile candidate paths
    search_paths = []
    # 1. check parent prompts/ (inside container: /app/prompts)
    parent_dir = os.path.dirname(current_dir)
    search_paths.append(os.path.join(parent_dir, "prompts", f"{prompt_name}.txt"))
    # 2. check grandparent prompts/ (local dev: workspace_root/prompts)
    grandparent_dir = os.path.dirname(parent_dir)
    search_paths.append(os.path.join(grandparent_dir, "prompts", f"{prompt_name}.txt"))
    # 3. check default absolute container directories
    search_paths.append(os.path.join("/app", "prompts", f"{prompt_name}.txt"))
    search_paths.append(os.path.join("/", "prompts", f"{prompt_name}.txt"))

    # Try loading from the first path that exists
    for prompt_path in search_paths:
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read prompt from existing path {prompt_path}: {str(e)}")
                raise e
                
    error_msg = f"Failed to locate prompt '{prompt_name}.txt'. Searched paths: {search_paths}"
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

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

async def call_aimlabs_async(system_instruction: str, prompt: str, json_mode: bool = False) -> str:
    """
    Calls the AIMALabs API (OpenAI-compatible) asynchronously with system instructions and a user prompt.
    Supports strict JSON output mode.
    Implements retries with exponential backoff on 429/quota limits.
    """
    import asyncio
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
            
            logger.debug(f"Calling AIMALabs Async (attempt {attempt}) with model {config.chat_model}")
            response = await async_client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate_limit" in err_str.lower()
            if is_rate_limit and attempt < max_retries:
                sleep_time = initial_delay * (backoff_factor ** (attempt - 1))
                logger.warning(
                    f"AIMALabs Async API rate limit hit (429/quota). "
                    f"Retrying attempt {attempt}/{max_retries} in {sleep_time}s... Error: {err_str}"
                )
                await asyncio.sleep(sleep_time)
            else:
                logger.error(f"Error calling AIMALabs Async on attempt {attempt}: {err_str}")
                raise e


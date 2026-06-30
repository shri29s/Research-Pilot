import os
import sys
from typing import NamedTuple
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class AppConfig(NamedTuple):
    aimlabs_api_key: str
    aimlabs_base_url: str
    chat_model: str
    embedding_model: str
    chroma_db_path: str
    max_critique_loops: int
    log_level: str
    semantic_scholar_limit: int
    arxiv_limit: int

def load_config() -> AppConfig:
    """Loads and validates app configuration from environment variables."""
    aimlabs_api_key = os.getenv("AIMLABS_API_KEY")
    if not aimlabs_api_key:
        print("ERROR: Missing required environment variable AIMLABS_API_KEY.", file=sys.stderr)
        print("Please copy .env.example to .env and populate it with your key.", file=sys.stderr)
        sys.exit(1)

    try:
        max_critique_loops = int(os.getenv("MAX_CRITIQUE_LOOPS", "2"))
    except ValueError:
        max_critique_loops = 2

    try:
        semantic_scholar_limit = int(os.getenv("SEMANTIC_SCHOLAR_LIMIT", "5"))
    except ValueError:
        semantic_scholar_limit = 5

    try:
        arxiv_limit = int(os.getenv("ARXIV_LIMIT", "5"))
    except ValueError:
        arxiv_limit = 5

    chroma_db_path = os.getenv("CHROMA_DB_PATH", "chroma_db/")
    try:
        os.makedirs(chroma_db_path, exist_ok=True)
        test_file = os.path.join(chroma_db_path, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, IOError):
        print(f"WARNING: Directory '{chroma_db_path}' is not writable. Falling back to '/tmp/chroma_db/'", file=sys.stderr)
        chroma_db_path = "/tmp/chroma_db/"
        os.makedirs(chroma_db_path, exist_ok=True)

    return AppConfig(
        aimlabs_api_key=aimlabs_api_key,
        aimlabs_base_url=os.getenv("AIMLABS_BASE_URL", "https://api.aimlapi.com/v1"),
        chat_model=os.getenv("AIMLABS_CHAT_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv("AIMLABS_EMBEDDING_MODEL", "text-embedding-3-small"),
        chroma_db_path=chroma_db_path,
        max_critique_loops=max_critique_loops,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        semantic_scholar_limit=semantic_scholar_limit,
        arxiv_limit=arxiv_limit
    )

# Singleton configuration instance
config = load_config()

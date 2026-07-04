import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# Load config.yaml
with open("config.yaml") as f:
    _cfg = yaml.safe_load(f) #_cfg is private therefore, other files should not use _cfg directly, they use the constants below eg LLM_MODEL, TEMPERATURE, etc.

# LLM settings
LLM_MODEL    = _cfg["llm"]["model"]
TEMPERATURE  = _cfg["llm"]["temperature"]
MAX_TOKENS   = _cfg["llm"]["max_tokens"]

# Splitter settings
CHUNK_SIZE    = _cfg["splitter"]["chunk_size"]
CHUNK_OVERLAP = _cfg["splitter"]["chunk_overlap"]

# Graph settings
MAX_RETRIES = _cfg["graph"]["max_retries"]

# Output settings
OUTPUT_DIR = _cfg["output"]["base_dir"]

# Secrets from .env — never hardcoded
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACCESS_TOKEN   = os.getenv("ACCESS_TOKEN")
OPC_PASSWORD   = os.getenv("OPC_PASSWORD")
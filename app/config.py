
import os
from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Data paths
CHUNK_PATH = os.getenv(
    "CHUNK_PATH",
    str(PROJECT_ROOT / "data/processed/chunks.json")
)

EMBEDDING_PATH = os.getenv(
    "EMBEDDING_PATH",
    str(PROJECT_ROOT / "data/processed/embeddings.npy")
)


# Model configuration
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "llama3.2:3b"
)


# Retrieval configuration
TOP_K = int(os.getenv("TOP_K", "3"))

RETRIEVAL_THRESHOLD = float(
    os.getenv("RETRIEVAL_THRESHOLD", "0.5")
)

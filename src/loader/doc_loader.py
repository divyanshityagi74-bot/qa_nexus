"""
doc_loader.py
=============
Loader layer — reads requirements file and returns LangChain Document objects.

Supported file types: .pdf, .txt, .md
Called by: src/nodes/load_document.py (LangGraph node)
"""

import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document

logger = logging.getLogger(__name__)


def load(filepath: str) -> List[Document]:
    """
    Reads a requirements file and returns a list of LangChain Document objects.

    Args:
        filepath: path to the requirements file (.pdf, .txt, or .md)

    Returns:
        List of LangChain Document objects

    Raises:
        FileNotFoundError: if file does not exist
        ValueError: if file type is not supported
    """
    path = Path(filepath)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(
            f"Requirements file not found: {filepath}"
        )

    suffix = path.suffix.lower()
    logger.info(f"Loading requirements file: {filepath} (type: {suffix})")

    # Detect file type and use correct loader
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))

    elif suffix in [".txt", ".md"]:
        loader = TextLoader(str(path), encoding="utf-8")

    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported types are: .pdf, .txt, .md"
        )

    docs = loader.load()
    logger.info(f"Successfully loaded {len(docs)} document(s)")

    return docs
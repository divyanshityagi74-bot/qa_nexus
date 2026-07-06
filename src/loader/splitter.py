"""
splitter.py
===========
Loader layer — splits LangChain Documents into smaller chunks for LLM processing.

Called by: src/nodes/load_document.py (LangGraph node)
"""

import logging
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from src.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def split(docs: List[Document]) -> List[Document]:
    """
    Splits a list of Documents into smaller chunks.

    Args:
        docs: list of LangChain Document objects from doc_loader.py

    Returns:
        List of smaller Document chunks
    """
    logger.info(
        f"Splitting {len(docs)} document(s) — "
        f"chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}"
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.split_documents(docs)

    logger.info(f"Produced {len(chunks)} chunk(s)")

    return chunks
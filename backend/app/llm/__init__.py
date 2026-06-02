"""LLM access layer.

The only place a provider SDK may be imported is ``client.py``. Everything else
talks to the provider through the thin, swappable ``LLMClient``.
"""

from app.llm.client import LLMClient, LLMError, get_llm_client

__all__ = ["LLMClient", "LLMError", "get_llm_client"]

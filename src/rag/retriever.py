"""RAG-lite retriever.

Loads a small knowledge base of role-specific interview patterns and
matches job descriptions to relevant roles using keyword matching.

This is "RAG-lite" — no vector database, no embeddings. Sprint 2 will
introduce real RAG with vector databases.
"""

import json
import re
from pathlib import Path


def load_knowledge_base(path: Path | None = None) -> dict:
    """Load the knowledge base JSON.

    Args:
        path: Optional path override. Defaults to data/knowledge_base.json
            relative to the project root.

    Returns:
        Dictionary mapping role names to their metadata.

    Raises:
        FileNotFoundError: If the knowledge base file doesn't exist.
        json.JSONDecodeError: If the file isn't valid JSON.
    """
    if path is None:
        # Derive project root from this file's location
        project_root = Path(__file__).resolve().parent.parent.parent
        path = project_root / "data" / "knowledge_base.json"

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _matches_keyword(text: str, keyword: str) -> bool:
    """Check if a keyword appears in text as a whole word.

    Args:
        text: The job description text (already lowercased).
        keyword: The keyword to search for (already lowercased).

    Returns:
        True if the keyword appears as a whole word.
    """
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text) is not None


def retrieve_context(
    job_description: str,
    knowledge_base: dict | None = None,
    max_roles: int = 3,
    min_matches: int = 2,
) -> str:
    """Retrieve relevant context for a job description.

    Matches the job description against role keywords in the knowledge
    base. Returns formatted context for injection into the LLM prompt.

    Args:
        job_description: The job description text.
        knowledge_base: Optional knowledge base override. If None, loads
            the default from data/knowledge_base.json.
        max_roles: Maximum number of roles to include.
        min_matches: Minimum number of keyword matches per role to count.

    Returns:
        Formatted context string. Empty string if no roles matched.
    """
    if knowledge_base is None:
        knowledge_base = load_knowledge_base()

    lower = job_description.lower()

    # Score each role by keyword match count
    scored: list[tuple[str, int, dict]] = []
    for role, data in knowledge_base.items():
        match_count = sum(
            1 for kw in data["keywords"] if _matches_keyword(lower, kw.lower())
        )
        if match_count >= min_matches:
            scored.append((role, match_count, data))

    if not scored:
        return ""

    # Sort by match count descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top_roles = scored[:max_roles]

    # Format context
    parts = []
    for role, _count, data in top_roles:
        parts.append(f"Role: {role}")
        parts.append(f"Common topics: {', '.join(data['common_topics'])}")
        parts.append("Example questions:")
        for q in data["question_patterns"][:3]:  # limit to 3 examples
            parts.append(f"  - {q}")
        parts.append("")

    return "\n".join(parts).strip()



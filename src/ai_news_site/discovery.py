import json
from pathlib import Path

from .models import CandidateEvent

_HN_TOPIC_KEYWORDS = {
    "Agents": ("agent", "agents", "agentic", "workflow", "langgraph", "openmanus", "copilot"),
    "Robotics": ("robot", "robotics", "warehouse", "humanoid", "figure"),
    "Open Source": ("open source", "open-source", "github", "repo", "repository", "release"),
    "AI": (
        "ai",
        "llm",
        "chatgpt",
        "gpt",
        "claude",
        "gemini",
        "openai",
        "model",
        "diffusion",
        "reinforcement learning",
    ),
}


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def _infer_hn_tags(title: str) -> list[str]:
    lowered = title.lower()
    tags = [
        tag for tag, keywords in _HN_TOPIC_KEYWORDS.items() if any(keyword in lowered for keyword in keywords)
    ]
    return tags or ["AI"]


def _is_relevant_hn_title(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keywords in _HN_TOPIC_KEYWORDS.values() for keyword in keywords)


def build_candidates(watchlist_path: Path, hn_titles: list[dict]) -> list[CandidateEvent]:
    watchlist = json.loads(Path(watchlist_path).read_text(encoding="utf-8"))
    seen_queries: set[str] = set()
    watchlist_candidates: list[CandidateEvent] = []
    hn_candidates: list[CandidateEvent] = []

    for item in watchlist:
        query = item["query"]
        seen_queries.add(query.lower())
        watchlist_candidates.append(
            CandidateEvent(
                event_id=_slugify(f"watch-{query}"),
                query=query,
                title=query,
                source="watchlist",
                occurred_at="scheduled",
                tags=item["tags"],
            )
        )

    for item in hn_titles:
        title = item["title"]
        lowered = title.lower()
        if any(query in lowered for query in seen_queries):
            continue
        if not _is_relevant_hn_title(title):
            continue
        hn_candidates.append(
            CandidateEvent(
                event_id=_slugify(f"hn-{title}"),
                query=title,
                title=title,
                source="hackernews",
                occurred_at=item["published_at"],
                tags=_infer_hn_tags(title),
            )
        )

    hn_candidates = sorted(hn_candidates, key=lambda item: item.occurred_at, reverse=True)
    return [*watchlist_candidates, *hn_candidates]

import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from .config import SiteConfig
from .discovery import build_candidates
from .editorial import build_card
from .models import ResearchFinding
from .publish_gate import should_publish
from .published_store import PublishedStore
from .site_builder import build_site

HN_TOPSTORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"


def _log_pipeline(message: str) -> None:
    print(f"[Pipeline] {message}", file=sys.stderr)


def _load_json(url: str):
    request = Request(url, headers={"User-Agent": "ai-news-site/0.1"})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_hackernews_titles(limit: int = 5) -> list[dict]:
    try:
        top_story_ids = _load_json(HN_TOPSTORIES_URL)
    except Exception as exc:
        _log_pipeline(f"hn_fetch_failed error={exc}")
        return []

    titles: list[dict] = []
    for story_id in top_story_ids[:limit]:
        try:
            item = _load_json(HN_ITEM_URL_TEMPLATE.format(story_id=story_id))
        except Exception:
            continue

        title = item.get("title")
        published_at = item.get("time")
        if not title or published_at is None:
            continue

        titles.append(
            {
                "title": title,
                "published_at": datetime.fromtimestamp(published_at, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
        )
    return titles


def discover_candidates(config: SiteConfig):
    return build_candidates(config.watchlist_path, fetch_hackernews_titles())


def research_candidate(config: SiteConfig, candidate):
    from .research_client import run_last30days

    return run_last30days(config.last30days_root, candidate)


def _coerce_findings(findings: list[ResearchFinding | dict]) -> list[ResearchFinding]:
    normalized: list[ResearchFinding] = []
    for finding in findings:
        if isinstance(finding, ResearchFinding):
            normalized.append(finding)
        else:
            normalized.append(ResearchFinding(**finding))
    return normalized


def publish_once(config: SiteConfig) -> dict:
    store = PublishedStore(config.state_db_path)
    store.init_db()
    published_count = 0

    for candidate in discover_candidates(config)[: config.max_cards_per_run]:
        try:
            findings = _coerce_findings(research_candidate(config, candidate))
            decision = should_publish(candidate, findings)
            if not decision.publish:
                sources = sorted({finding.source for finding in findings if finding.url})
                max_score = max((finding.score for finding in findings), default=0)
                _log_pipeline(
                    "candidate_skipped "
                    f"event_id={candidate.event_id} "
                    f"reason={decision.reason} "
                    f"findings={len(findings)} "
                    f"sources={','.join(sources) or 'none'} "
                    f"max_score={max_score}"
                )
                continue

            if store.has_card(candidate.event_id):
                _log_pipeline(f"candidate_duplicate event_id={candidate.event_id}")
                continue

            card = build_card(candidate, findings, datetime.now(timezone.utc).isoformat())
            store.upsert_card(card)
            published_count += 1
            _log_pipeline(
                f"candidate_published event_id={candidate.event_id} "
                f"topic_tags={','.join(card.topic_tags)} confidence={card.confidence_score}"
            )
        except Exception as exc:
            _log_pipeline(f"candidate_failed event_id={candidate.event_id} error={exc}")
            continue

    cards = store.list_latest(limit=100)
    build_site(config.output_dir, config.site_name, cards)
    _log_pipeline(
        f"published_count={published_count} rendered_count={len(cards)} output_dir={config.output_dir}"
    )
    return {"published_count": published_count, "output_dir": str(config.output_dir)}

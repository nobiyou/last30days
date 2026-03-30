from datetime import datetime, timezone

from .config import SiteConfig
from .discovery import build_candidates
from .editorial import build_card
from .models import ResearchFinding
from .publish_gate import should_publish
from .published_store import PublishedStore
from .site_builder import build_site


def discover_candidates(config: SiteConfig):
    return build_candidates(config.watchlist_path, [])


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
        findings = _coerce_findings(research_candidate(config, candidate))
        decision = should_publish(candidate, findings)
        if not decision.publish or store.has_card(candidate.event_id):
            continue

        card = build_card(candidate, findings, datetime.now(timezone.utc).isoformat())
        store.upsert_card(card)
        published_count += 1

    cards = store.list_latest(limit=100)
    build_site(config.output_dir, config.site_name, cards)
    return {"published_count": published_count, "output_dir": str(config.output_dir)}

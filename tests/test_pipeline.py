from pathlib import Path

from ai_news_site.config import SiteConfig
from ai_news_site.models import CandidateEvent, ResearchFinding
from ai_news_site import cli
from ai_news_site.pipeline import publish_once


def test_publish_once_builds_site_from_discovered_candidates(monkeypatch, tmp_path: Path):
    config = SiteConfig(
        site_name="Signal Radar",
        base_url="https://example.com",
        output_dir=tmp_path / "dist",
        state_db_path=tmp_path / "published.db",
        last30days_root=tmp_path / "last30days",
        watchlist_path=tmp_path / "topics.json",
        max_cards_per_run=3,
    )

    monkeypatch.setattr(
        "ai_news_site.pipeline.discover_candidates",
        lambda cfg: [
            CandidateEvent(
                "openmanus-release",
                "OpenManus release",
                "OpenManus release",
                "watchlist",
                "2026-03-30T10:00:00Z",
                ["Agents"],
            )
        ],
    )
    monkeypatch.setattr(
        "ai_news_site.pipeline.research_candidate",
        lambda cfg, candidate: [
            ResearchFinding(
                source="reddit",
                title=candidate.title,
                url="https://example.com",
                score=93,
                published_at="2026-03-30T10:00:00Z",
                summary="Planner update",
            )
        ],
    )

    result = publish_once(config)

    assert result["published_count"] == 1
    assert (tmp_path / "dist" / "index.html").exists()


def test_cli_publish_once_invokes_pipeline(monkeypatch):
    calls = []

    monkeypatch.setattr(cli, "load_config", lambda: object())
    monkeypatch.setattr(cli, "publish_once", lambda config: calls.append(config) or {"published_count": 1})

    exit_code = cli.main(["publish-once"])

    assert exit_code == 0
    assert len(calls) == 1

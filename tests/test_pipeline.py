from pathlib import Path

from ai_news_site import pipeline
from ai_news_site.config import SiteConfig
from ai_news_site.models import CandidateEvent, ResearchFinding
from ai_news_site import cli


def test_discover_candidates_passes_hn_titles_to_build_candidates(monkeypatch, tmp_path: Path):
    config = SiteConfig(
        site_name="Signal Radar",
        base_url="https://example.com",
        output_dir=tmp_path / "dist",
        state_db_path=tmp_path / "published.db",
        last30days_root=tmp_path / "last30days",
        watchlist_path=tmp_path / "topics.json",
        max_cards_per_run=3,
    )
    hn_titles = [{"title": "HN robotics launch", "published_at": "2026-03-30T10:00:00Z"}]
    seen = {}

    monkeypatch.setattr("ai_news_site.pipeline.fetch_hackernews_titles", lambda: hn_titles)
    monkeypatch.setattr(
        "ai_news_site.pipeline.build_candidates",
        lambda watchlist_path, trend_titles: seen.update(
            {"watchlist_path": watchlist_path, "trend_titles": trend_titles}
        )
        or [],
    )

    pipeline.discover_candidates(config)

    assert seen["watchlist_path"] == config.watchlist_path
    assert seen["trend_titles"] == hn_titles


def test_fetch_hackernews_titles_returns_empty_list_on_failure(monkeypatch):
    monkeypatch.setattr(
        "ai_news_site.pipeline.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("hn unavailable")),
        raising=False,
    )

    assert pipeline.fetch_hackernews_titles() == []


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

    result = pipeline.publish_once(config)

    assert result["published_count"] == 1
    assert (tmp_path / "dist" / "index.html").exists()


def test_publish_once_skips_failed_candidate_and_continues(monkeypatch, tmp_path: Path):
    config = SiteConfig(
        site_name="Signal Radar",
        base_url="https://example.com",
        output_dir=tmp_path / "dist",
        state_db_path=tmp_path / "published.db",
        last30days_root=tmp_path / "last30days",
        watchlist_path=tmp_path / "topics.json",
        max_cards_per_run=3,
    )
    failing = CandidateEvent(
        "openmanus-release",
        "OpenManus release",
        "OpenManus release",
        "watchlist",
        "2026-03-30T10:00:00Z",
        ["Agents"],
    )
    succeeding = CandidateEvent(
        "robotics-launch",
        "Robotics launch",
        "Robotics launch",
        "watchlist",
        "2026-03-30T10:05:00Z",
        ["Robotics"],
    )

    monkeypatch.setattr(
        "ai_news_site.pipeline.discover_candidates",
        lambda cfg: [failing, succeeding],
    )

    def fake_research(cfg, candidate):
        if candidate.event_id == failing.event_id:
            raise RuntimeError("research failed")
        return [
            ResearchFinding(
                source="reddit",
                title=candidate.title,
                url="https://example.com/robotics",
                score=95,
                published_at="2026-03-30T10:06:00Z",
                summary="Warehouse pilot lands",
            )
        ]

    monkeypatch.setattr("ai_news_site.pipeline.research_candidate", fake_research)

    result = pipeline.publish_once(config)

    assert result["published_count"] == 1
    assert (tmp_path / "dist" / "index.html").exists()
    assert "robotics-launch" in (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")


def test_cli_publish_once_invokes_pipeline(monkeypatch):
    calls = []

    monkeypatch.setattr(cli, "load_config", lambda: object())
    monkeypatch.setattr(cli, "publish_once", lambda config: calls.append(config) or {"published_count": 1})

    exit_code = cli.main(["publish-once"])

    assert exit_code == 0
    assert len(calls) == 1

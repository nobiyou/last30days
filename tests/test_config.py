from pathlib import Path

from ai_news_site.config import load_config
from ai_news_site.models import NewsCard


def test_load_config_reads_required_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_NEWS_SITE_NAME", "Signal Radar")
    monkeypatch.setenv("AI_NEWS_BASE_URL", "https://example.com")
    monkeypatch.setenv("AI_NEWS_OUTPUT_DIR", str(tmp_path / "dist"))
    monkeypatch.setenv("AI_NEWS_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("LAST30DAYS_ROOT", str(tmp_path / "last30days"))
    monkeypatch.setenv("AI_NEWS_WATCHLIST_PATH", str(tmp_path / "topics.json"))

    config = load_config()

    assert config.site_name == "Signal Radar"
    assert config.output_dir == tmp_path / "dist"
    assert config.last30days_root == tmp_path / "last30days"


def test_news_card_slug_is_stable():
    card = NewsCard(
        canonical_event_id="github-openmanus-release",
        title="OpenManus 发布新版本",
        summary="版本更新带来更好的任务规划。",
        why_it_matters="开发者可以更快验证 agent 工作流。",
        who_should_care="独立开发者",
        topic_tags=["Agents", "Open Source"],
        source_links=["https://example.com/openmanus"],
        confidence_score=0.92,
        published_at="2026-03-30T10:00:00Z",
    )

    assert card.slug == "github-openmanus-release"

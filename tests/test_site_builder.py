from pathlib import Path

from ai_news_site.models import NewsCard
from ai_news_site.site_builder import build_site


def test_build_site_writes_homepage_detail_and_topic_pages(tmp_path: Path):
    card = NewsCard(
        canonical_event_id="openmanus-release",
        title="OpenManus release",
        summary="新版本引发了社区关注。",
        why_it_matters="Agent 工作流验证成本更低。",
        who_should_care="独立开发者",
        topic_tags=["Agents", "Open Source"],
        source_links=["https://example.com/openmanus"],
        confidence_score=0.9,
        published_at="2026-03-30T10:30:00Z",
    )

    build_site(tmp_path, "Signal Radar", [card])

    index_html = (tmp_path / "index.html").read_text(encoding="utf-8")
    detail_html = (tmp_path / "news" / "openmanus-release.html").read_text(encoding="utf-8")
    topic_html = (tmp_path / "topics" / "agents.html").read_text(encoding="utf-8")
    css = (tmp_path / "site.css").read_text(encoding="utf-8")

    assert "Signal Radar" in index_html
    assert "OpenManus release" in index_html
    assert "site.css" in index_html
    assert "OpenManus release" in detail_html
    assert "Agent 工作流验证成本更低。" in detail_html
    assert "../site.css" in detail_html
    assert "Agents" in topic_html
    assert "OpenManus release" in topic_html
    assert "../site.css" in topic_html
    assert "--bg" in css

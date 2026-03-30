from pathlib import Path

from ai_news_site.models import NewsCard
from ai_news_site.published_store import PublishedStore


def test_store_upserts_and_lists_latest(tmp_path: Path):
    store = PublishedStore(tmp_path / "published.db")
    store.init_db()

    card = NewsCard(
        canonical_event_id="agentops-1",
        title="AgentOps 发布 1.0",
        event_type="版本发布",
        summary="发布了新的 tracing 功能。",
        key_signal="2 个来源、1 条证据，最高信号 0.88。",
        why_it_matters="Agent 可观测性更容易落地。",
        who_should_care="创业团队",
        topic_tags=["Agents"],
        source_links=["https://example.com/agentops"],
        confidence_score=0.88,
        published_at="2026-03-30T09:00:00Z",
    )

    store.upsert_card(card)

    assert store.has_card("agentops-1") is True
    latest = store.list_latest(limit=1)
    assert latest[0].title == "AgentOps 发布 1.0"
    assert latest[0].event_type == "版本发布"
    assert latest[0].key_signal == "2 个来源、1 条证据，最高信号 0.88。"

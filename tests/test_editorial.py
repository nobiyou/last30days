from ai_news_site.editorial import build_card
from ai_news_site.models import CandidateEvent, ResearchFinding
from ai_news_site.topic_router import route_topics


def test_route_topics_keeps_defaults_and_adds_signal_topics():
    tags = route_topics("OpenManus release for warehouse robots", ["Agents"])

    assert tags == ["Agents", "Open Source", "Robotics"]


def test_build_card_generates_short_publishable_news_card():
    candidate = CandidateEvent(
        event_id="openmanus-release",
        query="OpenManus release",
        title="OpenManus release",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents", "Open Source"],
    )
    findings = [
        ResearchFinding(
            "reddit",
            "OpenManus ships new planner",
            "https://a",
            88,
            "2026-03-30T10:00:00Z",
            "Planner update",
        ),
        ResearchFinding(
            "x",
            "OpenManus release gets traction",
            "https://b",
            91,
            "2026-03-30T10:05:00Z",
            "Strong community response",
        ),
    ]

    card = build_card(candidate, findings, "2026-03-30T10:30:00Z")

    assert card.title == "OpenManus release"
    assert card.event_type == "版本发布"
    assert card.summary.startswith("最近 7 天，OpenManus release")
    assert "2 个来源" in card.key_signal
    assert "开源" in card.why_it_matters
    assert "开发者工具" in card.who_should_care
    assert card.topic_tags == ["Agents", "Open Source"]
    assert card.source_links == ["https://b", "https://a"]
    assert card.confidence_score == 0.91
    assert card.published_at == "2026-03-30T10:30:00Z"


def test_build_card_bounds_summary_length_for_long_findings():
    candidate = CandidateEvent(
        event_id="robotics-launch",
        query="robotics launch",
        title="Robotics launch",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Robotics"],
    )
    findings = [
        ResearchFinding(
            "reddit",
            "Robotics launch",
            "https://a",
            88,
            "2026-03-30T10:00:00Z",
            "A" * 180,
        ),
        ResearchFinding(
            "x",
            "Robotics launch",
            "https://b",
            91,
            "2026-03-30T10:05:00Z",
            "B" * 180,
        ),
    ]

    card = build_card(candidate, findings, "2026-03-30T10:30:00Z")

    assert len(card.summary) <= 160
    assert not card.summary.endswith("；")
    assert "最近 7 天" in card.summary
    assert "1 个来源" in card.key_signal or "2 个来源" in card.key_signal

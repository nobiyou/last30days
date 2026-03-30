from ai_news_site.models import CandidateEvent, ResearchFinding
from ai_news_site.publish_gate import should_publish


def test_should_publish_when_multiple_sources_confirm_same_event():
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
            "OpenManus ships new release",
            "https://a",
            88,
            "2026-03-30T10:00:00Z",
            "Reddit thread",
        ),
        ResearchFinding(
            "x",
            "OpenManus release is getting traction",
            "https://b",
            91,
            "2026-03-30T10:05:00Z",
            "X post",
        ),
    ]

    decision = should_publish(candidate, findings)

    assert decision.publish is True
    assert decision.reason == "multi_source_confirmation"

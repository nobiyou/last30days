import json
from pathlib import Path

from ai_news_site.models import CandidateEvent, ResearchFinding
from ai_news_site.research_client import run_last30days
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


def test_run_last30days_parses_new_upstream_sources(monkeypatch, tmp_path: Path):
    candidate = CandidateEvent(
        event_id="openmanus-release",
        query="OpenManus release",
        title="OpenManus release",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents", "Open Source"],
    )

    payload = {
        "reddit": [
            {
                "title": "OpenManus gets traction",
                "url": "https://example.com/reddit",
                "score": 42,
                "date": "2026-03-30T08:00:00Z",
                "summary": "reddit summary",
            }
        ],
        "tiktok": [
            {
                "title": "OpenManus demo on TikTok",
                "url": "https://example.com/tiktok",
                "score": 55,
                "date": "2026-03-30T08:05:00Z",
                "summary": "tiktok summary",
            }
        ],
        "instagram": [
            {
                "title": "OpenManus on Instagram",
                "url": "https://example.com/instagram",
                "score": 48,
                "date": "2026-03-30T08:10:00Z",
                "summary": "instagram summary",
            }
        ],
        "bluesky": [
            {
                "title": "OpenManus on Bluesky",
                "url": "https://example.com/bluesky",
                "score": 61,
                "date": "2026-03-30T08:15:00Z",
                "summary": "bluesky summary",
            }
        ],
    }

    def fake_run(*args, **kwargs):
        class Result:
            stdout = json.dumps(payload)

        return Result()

    monkeypatch.setattr("ai_news_site.research_client.subprocess.run", fake_run)

    findings = run_last30days(tmp_path, candidate)

    assert {item.source for item in findings} >= {"reddit", "tiktok", "instagram", "bluesky"}
    assert any(item.title == "OpenManus demo on TikTok" for item in findings)


def test_run_last30days_requests_utf8_decoding(monkeypatch, tmp_path: Path):
    candidate = CandidateEvent(
        event_id="langgraph-update",
        query="LangGraph update",
        title="LangGraph update",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents"],
    )
    seen = {}

    def fake_run(*args, **kwargs):
        seen.update(kwargs)

        class Result:
            stdout = json.dumps({"reddit": []}, ensure_ascii=False)

        return Result()

    monkeypatch.setattr("ai_news_site.research_client.subprocess.run", fake_run)

    run_last30days(tmp_path, candidate)

    assert seen["text"] is True
    assert seen["encoding"] == "utf-8"

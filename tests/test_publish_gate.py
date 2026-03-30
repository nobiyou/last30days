import json
import subprocess
from pathlib import Path
import pytest

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


def test_should_publish_when_hackernews_has_strong_single_source_breakout():
    candidate = CandidateEvent(
        event_id="hn-agent-postmortem",
        query="Agent postmortem",
        title="Agent postmortem",
        source="hackernews",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents"],
    )

    findings = [
        ResearchFinding(
            "hackernews",
            "Agent postmortem gets traction",
            "https://news.ycombinator.com/item?id=1",
            85,
            "2026-03-30T10:00:00Z",
            "HN story",
        )
    ]

    decision = should_publish(candidate, findings)

    assert decision.publish is True
    assert decision.reason == "trusted_hackernews_breakout"


def test_should_not_publish_generic_single_source_reddit_breakout_below_global_threshold():
    candidate = CandidateEvent(
        event_id="reddit-agent-post",
        query="Agent post",
        title="Agent post",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents"],
    )

    findings = [
        ResearchFinding(
            "reddit",
            "Agent post gets traction",
            "https://reddit.com/r/test/1",
            85,
            "2026-03-30T10:00:00Z",
            "Reddit thread",
        )
    ]

    decision = should_publish(candidate, findings)

    assert decision.publish is False
    assert decision.reason == "insufficient_signal"


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


def test_run_last30days_extracts_json_from_mixed_stdout(monkeypatch, tmp_path: Path):
    candidate = CandidateEvent(
        event_id="langgraph-update",
        query="LangGraph update",
        title="LangGraph update",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Agents"],
    )
    payload = {
        "reddit": [
            {
                "title": "LangGraph discussion",
                "url": "https://example.com/reddit",
                "score": 51,
                "date": "2026-03-30T08:00:00Z",
                "summary": "reddit summary",
            }
        ]
    }

    def fake_run(*args, **kwargs):
        class Result:
            stdout = (
                "[REDDIT WARNING] No output text found in OpenAI response.\n"
                + json.dumps(payload)
                + "\n\n### WEBSEARCH REQUIRED ###\n"
            )

        return Result()

    monkeypatch.setattr("ai_news_site.research_client.subprocess.run", fake_run)

    findings = run_last30days(tmp_path, candidate)

    assert len(findings) == 1
    assert findings[0].title == "LangGraph discussion"


def test_run_last30days_surfaces_subprocess_stderr(monkeypatch, tmp_path: Path):
    candidate = CandidateEvent(
        event_id="figure-robotics",
        query="Figure robotics",
        title="Figure robotics",
        source="watchlist",
        occurred_at="2026-03-30T10:00:00Z",
        tags=["Robotics"],
    )

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=kwargs.get("args", ["python"]),
            stderr="Traceback: upstream failed hard",
        )

    monkeypatch.setattr("ai_news_site.research_client.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="figure-robotics"):
        run_last30days(tmp_path, candidate)

    with pytest.raises(RuntimeError, match="upstream failed hard"):
        run_last30days(tmp_path, candidate)

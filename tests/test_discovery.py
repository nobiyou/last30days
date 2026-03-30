import json

from ai_news_site.discovery import build_candidates


def test_build_candidates_merges_watchlist_and_hn_without_duplicates(tmp_path):
    watchlist_path = tmp_path / "topics.json"
    watchlist_path.write_text(
        json.dumps(
            [
                {"query": "OpenManus", "tags": ["Agents", "Open Source"]},
                {"query": "Figure robotics", "tags": ["Robotics"]},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    hn_titles = [
        {"title": "OpenManus is trending in Hacker News", "published_at": "2026-03-30T08:00:00Z"},
        {"title": "New robotics startup ships warehouse pilot", "published_at": "2026-03-30T08:10:00Z"},
    ]

    candidates = build_candidates(watchlist_path, hn_titles)

    assert len(candidates) == 3
    assert candidates[0].query == "OpenManus"
    assert any(item.source == "hackernews" for item in candidates)

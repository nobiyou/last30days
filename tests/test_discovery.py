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
        {"title": "New robotics startup ships warehouse pilot", "published_at": "2026-03-30T08:10:00Z"},
        {"title": "OpenManus is trending in Hacker News", "published_at": "2026-03-30T08:00:00Z"},
        {"title": "AI hardware company raises seed round", "published_at": "2026-03-30T08:30:00Z"},
    ]

    candidates = build_candidates(watchlist_path, hn_titles)

    assert len(candidates) == 4
    assert [(item.source, item.query) for item in candidates] == [
        ("watchlist", "OpenManus"),
        ("watchlist", "Figure robotics"),
        ("hackernews", "AI hardware company raises seed round"),
        ("hackernews", "New robotics startup ships warehouse pilot"),
    ]


def test_build_candidates_filters_out_unrelated_hn_titles(tmp_path):
    watchlist_path = tmp_path / "topics.json"
    watchlist_path.write_text(
        json.dumps(
            [
                {"query": "OpenManus", "tags": ["Agents", "Open Source"]},
                {"query": "LangGraph", "tags": ["Agents"]},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    hn_titles = [
        {"title": "VHDL's Crown Jewel", "published_at": "2026-03-30T08:10:00Z"},
        {"title": "The curious case of retro demo scene graphics", "published_at": "2026-03-30T08:20:00Z"},
        {
            "title": "Open source agent framework ships release",
            "published_at": "2026-03-30T08:30:00Z",
        },
        {"title": "Figure robotics expands warehouse pilot", "published_at": "2026-03-30T08:40:00Z"},
    ]

    candidates = build_candidates(watchlist_path, hn_titles)

    assert [(item.source, item.query) for item in candidates] == [
        ("watchlist", "OpenManus"),
        ("watchlist", "LangGraph"),
        ("hackernews", "Figure robotics expands warehouse pilot"),
        ("hackernews", "Open source agent framework ships release"),
    ]

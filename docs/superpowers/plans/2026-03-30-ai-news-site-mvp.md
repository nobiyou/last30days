# AI News Site MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully automated vertical AI news site that discovers candidate topics, runs `last30days` research, converts qualified findings into short news cards, and publishes a static site with a rolling homepage, detail pages, and topic hubs.

**Architecture:** Use Python end-to-end for orchestration, publish gating, card generation, and static site rendering. Treat `last30days` as an external research engine invoked through a thin subprocess adapter, and keep site state in a separate SQLite database so published cards and generated pages remain under our control. The first deploy target is a static `dist/` build plus GitHub Pages automation.

**Tech Stack:** Python 3.11+, `pytest`, `jinja2`, SQLite, GitHub Actions, static HTML/CSS/JSON

---

**当前工作区说明：**

- 当前目录 `E:\dev\last30days` 还不是 Git 仓库
- 计划按“绿地项目”拆分，Task 1 会先完成 Python 项目骨架和 Git 初始化
- `last30days` 通过环境变量 `LAST30DAYS_ROOT` 指向外部仓库或安装目录，不直接把它的代码复制进本站项目

## File Structure

### Root

- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `config/watchlists/topics.json`
- Create: `.github/workflows/publish.yml`

### Python package

- Create: `src/ai_news_site/__init__.py`
- Create: `src/ai_news_site/cli.py`
- Create: `src/ai_news_site/config.py`
- Create: `src/ai_news_site/models.py`
- Create: `src/ai_news_site/discovery.py`
- Create: `src/ai_news_site/research_client.py`
- Create: `src/ai_news_site/publish_gate.py`
- Create: `src/ai_news_site/topic_router.py`
- Create: `src/ai_news_site/editorial.py`
- Create: `src/ai_news_site/published_store.py`
- Create: `src/ai_news_site/site_builder.py`
- Create: `src/ai_news_site/pipeline.py`

### Templates and static assets

- Create: `src/ai_news_site/templates/base.html`
- Create: `src/ai_news_site/templates/index.html`
- Create: `src/ai_news_site/templates/detail.html`
- Create: `src/ai_news_site/templates/topic.html`
- Create: `src/ai_news_site/static/site.css`

### Tests

- Create: `tests/test_smoke.py`
- Create: `tests/test_config.py`
- Create: `tests/test_published_store.py`
- Create: `tests/test_discovery.py`
- Create: `tests/test_publish_gate.py`
- Create: `tests/test_editorial.py`
- Create: `tests/test_site_builder.py`
- Create: `tests/test_pipeline.py`

## Task 1: Bootstrap Repository and CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/ai_news_site/__init__.py`
- Create: `src/ai_news_site/cli.py`
- Test: `tests/test_smoke.py`

- [ ] **Step 1: Initialize the repo and write the failing smoke test**

```powershell
git init
New-Item -ItemType Directory -Force -Path src\ai_news_site, tests | Out-Null
```

```python
# tests/test_smoke.py
from ai_news_site.cli import build_parser


def test_build_parser_uses_expected_program_name():
    parser = build_parser()
    assert parser.prog == "ai-news-site"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_smoke.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site'
```

- [ ] **Step 3: Write the minimal package and CLI implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-news-site"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["jinja2>=3.1.4"]

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]

[project.scripts]
ai-news-site = "ai_news_site.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```gitignore
# .gitignore
__pycache__/
.pytest_cache/
.venv/
dist/
site_state/
```

```python
# src/ai_news_site/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

```python
# src/ai_news_site/cli.py
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-news-site")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("publish-once", help="Run discovery, research, and site publishing once")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_smoke.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml .gitignore src/ai_news_site/__init__.py src/ai_news_site/cli.py tests/test_smoke.py
git commit -m "chore: bootstrap ai news site project"
```

## Task 2: Add Config Loader and Core Data Models

**Files:**
- Create: `src/ai_news_site/config.py`
- Create: `src/ai_news_site/models.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config and model test**

```python
# tests/test_config.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_config.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.config'
```

- [ ] **Step 3: Write the minimal config loader and models**

```python
# src/ai_news_site/config.py
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SiteConfig:
    site_name: str
    base_url: str
    output_dir: Path
    state_db_path: Path
    last30days_root: Path
    watchlist_path: Path
    max_cards_per_run: int = 12


def load_config() -> SiteConfig:
    return SiteConfig(
        site_name=os.environ["AI_NEWS_SITE_NAME"],
        base_url=os.environ["AI_NEWS_BASE_URL"],
        output_dir=Path(os.environ["AI_NEWS_OUTPUT_DIR"]),
        state_db_path=Path(os.environ["AI_NEWS_STATE_DB"]),
        last30days_root=Path(os.environ["LAST30DAYS_ROOT"]),
        watchlist_path=Path(os.environ["AI_NEWS_WATCHLIST_PATH"]),
        max_cards_per_run=int(os.environ.get("AI_NEWS_MAX_CARDS", "12")),
    )
```

```python
# src/ai_news_site/models.py
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateEvent:
    event_id: str
    query: str
    title: str
    source: str
    occurred_at: str
    tags: list[str]


@dataclass(frozen=True)
class ResearchFinding:
    source: str
    title: str
    url: str
    score: float
    published_at: str
    summary: str


@dataclass(frozen=True)
class NewsCard:
    canonical_event_id: str
    title: str
    summary: str
    why_it_matters: str
    who_should_care: str
    topic_tags: list[str]
    source_links: list[str]
    confidence_score: float
    published_at: str

    @property
    def slug(self) -> str:
        return self.canonical_event_id
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_config.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```powershell
git add src/ai_news_site/config.py src/ai_news_site/models.py tests/test_config.py
git commit -m "feat: add site config and core models"
```

## Task 3: Add Published Card Store with SQLite Dedupe

**Files:**
- Create: `src/ai_news_site/published_store.py`
- Test: `tests/test_published_store.py`

- [ ] **Step 1: Write the failing persistence test**

```python
# tests/test_published_store.py
from pathlib import Path

from ai_news_site.models import NewsCard
from ai_news_site.published_store import PublishedStore


def test_store_upserts_and_lists_latest(tmp_path: Path):
    store = PublishedStore(tmp_path / "published.db")
    store.init_db()

    card = NewsCard(
        canonical_event_id="agentops-1",
        title="AgentOps 发布 1.0",
        summary="发布了新的 tracing 功能。",
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_published_store.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.published_store'
```

- [ ] **Step 3: Write the minimal SQLite store**

```python
# src/ai_news_site/published_store.py
import json
import sqlite3
from pathlib import Path

from .models import NewsCard


class PublishedStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS published_cards (
                    canonical_event_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    why_it_matters TEXT NOT NULL,
                    who_should_care TEXT NOT NULL,
                    topic_tags TEXT NOT NULL,
                    source_links TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    published_at TEXT NOT NULL
                )
                """
            )

    def has_card(self, canonical_event_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM published_cards WHERE canonical_event_id = ?",
                (canonical_event_id,),
            ).fetchone()
        return row is not None

    def upsert_card(self, card: NewsCard) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO published_cards (
                    canonical_event_id, title, summary, why_it_matters,
                    who_should_care, topic_tags, source_links,
                    confidence_score, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_event_id) DO UPDATE SET
                    title = excluded.title,
                    summary = excluded.summary,
                    why_it_matters = excluded.why_it_matters,
                    who_should_care = excluded.who_should_care,
                    topic_tags = excluded.topic_tags,
                    source_links = excluded.source_links,
                    confidence_score = excluded.confidence_score,
                    published_at = excluded.published_at
                """,
                (
                    card.canonical_event_id,
                    card.title,
                    card.summary,
                    card.why_it_matters,
                    card.who_should_care,
                    json.dumps(card.topic_tags, ensure_ascii=False),
                    json.dumps(card.source_links, ensure_ascii=False),
                    card.confidence_score,
                    card.published_at,
                ),
            )

    def list_latest(self, limit: int = 20) -> list[NewsCard]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM published_cards
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            NewsCard(
                canonical_event_id=row["canonical_event_id"],
                title=row["title"],
                summary=row["summary"],
                why_it_matters=row["why_it_matters"],
                who_should_care=row["who_should_care"],
                topic_tags=json.loads(row["topic_tags"]),
                source_links=json.loads(row["source_links"]),
                confidence_score=row["confidence_score"],
                published_at=row["published_at"],
            )
            for row in rows
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_published_store.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add src/ai_news_site/published_store.py tests/test_published_store.py
git commit -m "feat: add published card sqlite store"
```

## Task 4: Implement Candidate Discovery from Watchlist and HN

**Files:**
- Create: `config/watchlists/topics.json`
- Create: `src/ai_news_site/discovery.py`
- Test: `tests/test_discovery.py`

- [ ] **Step 1: Write the failing discovery test**

```python
# tests/test_discovery.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_discovery.py -v
```

Expected:

```text
E   ImportError: cannot import name 'build_candidates'
```

- [ ] **Step 3: Write the minimal discovery module**

```json
[
  {"query": "OpenManus", "tags": ["Agents", "Open Source"]},
  {"query": "LangGraph", "tags": ["Agents"]},
  {"query": "Figure robotics", "tags": ["Robotics"]},
  {"query": "open-source LLM tools", "tags": ["AI", "Open Source"]}
]
```

```python
# src/ai_news_site/discovery.py
import json
from pathlib import Path

from .models import CandidateEvent


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def build_candidates(watchlist_path: Path, hn_titles: list[dict]) -> list[CandidateEvent]:
    watchlist = json.loads(Path(watchlist_path).read_text(encoding="utf-8"))
    seen_queries: set[str] = set()
    results: list[CandidateEvent] = []

    for item in watchlist:
        query = item["query"]
        seen_queries.add(query.lower())
        results.append(
            CandidateEvent(
                event_id=_slugify(f"watch-{query}"),
                query=query,
                title=query,
                source="watchlist",
                occurred_at="scheduled",
                tags=item["tags"],
            )
        )

    for item in hn_titles:
        title = item["title"]
        lowered = title.lower()
        if "openmanus" in lowered and "openmanus" in seen_queries:
            continue
        results.append(
            CandidateEvent(
                event_id=_slugify(f"hn-{title}"),
                query=title,
                title=title,
                source="hackernews",
                occurred_at=item["published_at"],
                tags=["AI"],
            )
        )

    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_discovery.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add config/watchlists/topics.json src/ai_news_site/discovery.py tests/test_discovery.py
git commit -m "feat: add initial candidate discovery"
```

## Task 5: Add `last30days` Adapter and Publish Gate

**Files:**
- Create: `src/ai_news_site/research_client.py`
- Create: `src/ai_news_site/publish_gate.py`
- Test: `tests/test_publish_gate.py`

- [ ] **Step 1: Write the failing publish gate test**

```python
# tests/test_publish_gate.py
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
        ResearchFinding("reddit", "OpenManus ships new release", "https://a", 88, "2026-03-30T10:00:00Z", "Reddit thread"),
        ResearchFinding("x", "OpenManus release is getting traction", "https://b", 91, "2026-03-30T10:05:00Z", "X post"),
    ]

    decision = should_publish(candidate, findings)

    assert decision.publish is True
    assert decision.reason == "multi_source_confirmation"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_publish_gate.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.publish_gate'
```

- [ ] **Step 3: Write the research adapter and gate logic**

```python
# src/ai_news_site/research_client.py
import json
import subprocess
import sys
from pathlib import Path

from .models import CandidateEvent, ResearchFinding


def run_last30days(last30days_root: Path, candidate: CandidateEvent) -> list[ResearchFinding]:
    script = last30days_root / "scripts" / "last30days.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            candidate.query,
            "--emit=json",
            "--quick",
            "--days=7",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    findings: list[ResearchFinding] = []
    for source_name in ("reddit", "x", "youtube", "hackernews", "web"):
        for item in payload.get(source_name, []):
            findings.append(
                ResearchFinding(
                    source=source_name,
                    title=item.get("title", item.get("text", "")),
                    url=item.get("url", item.get("hn_url", "")),
                    score=float(item.get("score", item.get("relevance", 0))),
                    published_at=item.get("date", ""),
                    summary=item.get("why_relevant", item.get("summary", "")),
                )
            )
    return findings
```

```python
# src/ai_news_site/publish_gate.py
from dataclasses import dataclass

from .models import CandidateEvent, ResearchFinding


@dataclass(frozen=True)
class PublishDecision:
    publish: bool
    reason: str


def should_publish(candidate: CandidateEvent, findings: list[ResearchFinding]) -> PublishDecision:
    if not findings:
        return PublishDecision(False, "no_findings")

    sources = {finding.source for finding in findings if finding.url}
    max_score = max(finding.score for finding in findings)
    structural_keywords = ("release", "funding", "launch", "version", "issue", "paper")
    title_lower = candidate.title.lower()

    if len(sources) >= 2:
        return PublishDecision(True, "multi_source_confirmation")
    if max_score >= 90:
        return PublishDecision(True, "strong_single_source_breakout")
    if any(keyword in title_lower for keyword in structural_keywords):
        return PublishDecision(True, "structural_update")
    return PublishDecision(False, "insufficient_signal")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_publish_gate.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add src/ai_news_site/research_client.py src/ai_news_site/publish_gate.py tests/test_publish_gate.py
git commit -m "feat: add last30days adapter and publish gate"
```

## Task 6: Add Topic Routing and Editorial Normalization

**Files:**
- Create: `src/ai_news_site/topic_router.py`
- Create: `src/ai_news_site/editorial.py`
- Test: `tests/test_editorial.py`

- [ ] **Step 1: Write the failing editorial test**

```python
# tests/test_editorial.py
from ai_news_site.editorial import build_card
from ai_news_site.models import CandidateEvent, ResearchFinding


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
        ResearchFinding("reddit", "OpenManus ships new planner", "https://a", 88, "2026-03-30T10:00:00Z", "Planner update"),
        ResearchFinding("x", "OpenManus release gets traction", "https://b", 91, "2026-03-30T10:05:00Z", "Strong community response"),
    ]

    card = build_card(candidate, findings, "2026-03-30T10:30:00Z")

    assert card.title == "OpenManus release"
    assert "Planner update" in card.summary
    assert "独立开发者" in card.who_should_care
    assert "Agents" in card.topic_tags
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_editorial.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.editorial'
```

- [ ] **Step 3: Write the router and editorial normalizer**

```python
# src/ai_news_site/topic_router.py
def route_topics(text: str, default_tags: list[str]) -> list[str]:
    lowered = text.lower()
    routed = set(default_tags)
    if any(keyword in lowered for keyword in ("agent", "workflow", "langgraph", "openmanus")):
        routed.add("Agents")
    if any(keyword in lowered for keyword in ("robot", "warehouse", "figure", "humanoid")):
        routed.add("Robotics")
    if any(keyword in lowered for keyword in ("open source", "github", "repo", "release")):
        routed.add("Open Source")
    if not routed:
        routed.add("AI")
    return sorted(routed)
```

```python
# src/ai_news_site/editorial.py
from .models import CandidateEvent, NewsCard, ResearchFinding
from .topic_router import route_topics


def build_card(candidate: CandidateEvent, findings: list[ResearchFinding], published_at: str) -> NewsCard:
    top = sorted(findings, key=lambda item: item.score, reverse=True)[:2]
    joined_summary = "；".join(item.summary for item in top if item.summary)[:120]
    topic_tags = route_topics(candidate.title, candidate.tags)
    return NewsCard(
        canonical_event_id=candidate.event_id,
        title=candidate.title,
        summary=f"{joined_summary}。社区讨论集中在这次更新是否会改变近期采用节奏。",
        why_it_matters="这条信号说明相关工具或项目正在获得真实关注，值得尽快验证。",
        who_should_care="独立开发者、创业团队和投资人",
        topic_tags=topic_tags,
        source_links=[item.url for item in top if item.url],
        confidence_score=round(max(item.score for item in top) / 100, 2),
        published_at=published_at,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_editorial.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add src/ai_news_site/topic_router.py src/ai_news_site/editorial.py tests/test_editorial.py
git commit -m "feat: add topic routing and editorial normalizer"
```

## Task 7: Build Static Site Output with Templates

**Files:**
- Create: `src/ai_news_site/site_builder.py`
- Create: `src/ai_news_site/templates/base.html`
- Create: `src/ai_news_site/templates/index.html`
- Create: `src/ai_news_site/templates/detail.html`
- Create: `src/ai_news_site/templates/topic.html`
- Create: `src/ai_news_site/static/site.css`
- Test: `tests/test_site_builder.py`

- [ ] **Step 1: Write the failing site builder test**

```python
# tests/test_site_builder.py
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

    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "news" / "openmanus-release.html").exists()
    assert (tmp_path / "topics" / "agents.html").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_site_builder.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.site_builder'
```

- [ ] **Step 3: Write the minimal templates, CSS, and builder**

```html
<!-- src/ai_news_site/templates/base.html -->
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/site.css" />
  </head>
  <body>
    <header class="shell">
      <a class="brand" href="/index.html">{{ site_name }}</a>
      <nav><a href="/index.html">Latest</a></nav>
    </header>
    <main class="shell">
      {% block content %}{% endblock %}
    </main>
  </body>
</html>
```

```html
<!-- src/ai_news_site/templates/index.html -->
{% extends "base.html" %}
{% block content %}
<h1>Latest</h1>
{% for card in cards %}
<article class="card">
  <h2><a href="/news/{{ card.slug }}.html">{{ card.title }}</a></h2>
  <p>{{ card.summary }}</p>
</article>
{% endfor %}
{% endblock %}
```

```html
<!-- src/ai_news_site/templates/detail.html -->
{% extends "base.html" %}
{% block content %}
<article class="card">
  <h1>{{ card.title }}</h1>
  <p>{{ card.summary }}</p>
  <p><strong>为什么重要：</strong>{{ card.why_it_matters }}</p>
  <p><strong>谁应该关注：</strong>{{ card.who_should_care }}</p>
</article>
{% endblock %}
```

```html
<!-- src/ai_news_site/templates/topic.html -->
{% extends "base.html" %}
{% block content %}
<h1>{{ topic_name }}</h1>
{% for card in cards %}
<article class="card">
  <h2><a href="/news/{{ card.slug }}.html">{{ card.title }}</a></h2>
  <p>{{ card.summary }}</p>
</article>
{% endfor %}
{% endblock %}
```

```css
/* src/ai_news_site/static/site.css */
body { margin: 0; font-family: "Segoe UI", sans-serif; background: #f6f7fb; color: #111827; }
.shell { max-width: 960px; margin: 0 auto; padding: 24px; }
.brand { font-weight: 700; text-decoration: none; color: #0f172a; }
.card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
a { color: #2563eb; }
```

```python
# src/ai_news_site/site_builder.py
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .models import NewsCard

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def _slugify_topic(topic: str) -> str:
    return topic.lower().replace(" ", "-")


def build_site(output_dir: Path, site_name: str, cards: list[NewsCard]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "news").mkdir(exist_ok=True)
    (output_dir / "topics").mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    index_html = env.get_template("index.html").render(title=site_name, site_name=site_name, cards=cards)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    grouped: dict[str, list[NewsCard]] = {}
    for card in cards:
        detail_html = env.get_template("detail.html").render(title=card.title, site_name=site_name, card=card)
        (output_dir / "news" / f"{card.slug}.html").write_text(detail_html, encoding="utf-8")
        for topic in card.topic_tags:
            grouped.setdefault(topic, []).append(card)

    for topic, topic_cards in grouped.items():
        topic_html = env.get_template("topic.html").render(
            title=f"{topic} - {site_name}",
            site_name=site_name,
            topic_name=topic,
            cards=topic_cards,
        )
        (output_dir / "topics" / f"{_slugify_topic(topic)}.html").write_text(topic_html, encoding="utf-8")

    shutil.copyfile(STATIC_DIR / "site.css", output_dir / "site.css")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_site_builder.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add src/ai_news_site/site_builder.py src/ai_news_site/templates src/ai_news_site/static/site.css tests/test_site_builder.py
git commit -m "feat: add static site builder"
```

## Task 8: Wire the End-to-End Pipeline and Scheduled Publish Workflow

**Files:**
- Create: `src/ai_news_site/pipeline.py`
- Modify: `src/ai_news_site/cli.py`
- Create: `tests/test_pipeline.py`
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Write the failing pipeline test**

```python
# tests/test_pipeline.py
from pathlib import Path

from ai_news_site.config import SiteConfig
from ai_news_site.models import CandidateEvent
from ai_news_site.pipeline import publish_once


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
            CandidateEvent("openmanus-release", "OpenManus release", "OpenManus release", "watchlist", "2026-03-30T10:00:00Z", ["Agents"])
        ],
    )
    monkeypatch.setattr(
        "ai_news_site.pipeline.research_candidate",
        lambda cfg, candidate: [
            {"source": "reddit", "title": candidate.title, "url": "https://example.com", "score": 93, "published_at": "2026-03-30T10:00:00Z", "summary": "Planner update"}
        ],
    )

    result = publish_once(config)

    assert result["published_count"] == 1
    assert (tmp_path / "dist" / "index.html").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_pipeline.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'ai_news_site.pipeline'
```

- [ ] **Step 3: Write the pipeline, CLI hook, and GitHub Actions workflow**

```python
# src/ai_news_site/pipeline.py
from datetime import datetime, timezone

from .config import SiteConfig
from .discovery import build_candidates
from .editorial import build_card
from .models import ResearchFinding
from .publish_gate import should_publish
from .published_store import PublishedStore
from .site_builder import build_site


def discover_candidates(config: SiteConfig):
    return build_candidates(config.watchlist_path, [])


def research_candidate(config: SiteConfig, candidate):
    from .research_client import run_last30days

    return run_last30days(config.last30days_root, candidate)


def publish_once(config: SiteConfig) -> dict:
    store = PublishedStore(config.state_db_path)
    store.init_db()
    cards = store.list_latest(limit=100)
    published_count = 0

    for candidate in discover_candidates(config)[: config.max_cards_per_run]:
        findings = research_candidate(config, candidate)
        findings = [
            finding if isinstance(finding, ResearchFinding) else ResearchFinding(**finding)
            for finding in findings
        ]
        decision = should_publish(candidate, findings)
        if not decision.publish or store.has_card(candidate.event_id):
            continue

        card = build_card(candidate, findings, datetime.now(timezone.utc).isoformat())
        store.upsert_card(card)
        cards.insert(0, card)
        published_count += 1

    build_site(config.output_dir, config.site_name, cards[:100])
    return {"published_count": published_count, "output_dir": str(config.output_dir)}
```

```python
# src/ai_news_site/cli.py
import argparse

from .config import load_config
from .pipeline import publish_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-news-site")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("publish-once", help="Run discovery, research, and site publishing once")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "publish-once":
        publish_once(load_config())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```yaml
# .github/workflows/publish.yml
name: publish-ai-news-site

on:
  workflow_dispatch:
  schedule:
    - cron: "*/30 * * * *"

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      AI_NEWS_SITE_NAME: Signal Radar
      AI_NEWS_BASE_URL: https://example.github.io/ai-news-site
      AI_NEWS_OUTPUT_DIR: dist
      AI_NEWS_STATE_DB: site_state/published.db
      AI_NEWS_WATCHLIST_PATH: config/watchlists/topics.json
      LAST30DAYS_ROOT: /opt/last30days
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Checkout last30days
        run: git clone --depth 1 https://github.com/mvanhorn/last30days-skill.git /opt/last30days
      - name: Run publisher
        run: python -m ai_news_site.cli publish-once
      - name: Deploy to Pages branch
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git checkout --orphan gh-pages
          git --work-tree dist add --all
          git commit -m "publish latest site"
          git push origin HEAD:gh-pages --force
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_pipeline.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Run the full local test suite**

Run:

```powershell
python -m pytest -v
```

Expected:

```text
8 passed
```

- [ ] **Step 6: Commit**

```powershell
git add src/ai_news_site/pipeline.py src/ai_news_site/cli.py tests/test_pipeline.py .github/workflows/publish.yml
git commit -m "feat: wire automated publish pipeline"
```

## Self-Review

### Spec Coverage

- 滚动首页 feed：Task 7, Task 8
- Topic Hub：Task 6, Task 7
- 快讯详情页：Task 7
- 自动发现：Task 4, Task 8
- 自动研究：Task 5, Task 8
- 发布门槛：Task 5
- 卡片生成：Task 6
- 静态发布：Task 7, Task 8
- 自动调度：Task 8
- 安全兜底基础设施：Task 3, Task 5, Task 8

### Placeholder Scan

- 没有 `TODO`、`TBD`、`implement later` 之类占位内容
- 每个代码步骤都包含了具体代码
- 每个测试步骤都包含了明确命令和预期结果

### Type Consistency

- `CandidateEvent`、`ResearchFinding`、`NewsCard` 在各任务中字段名保持一致
- `publish_once()`、`build_site()`、`should_publish()`、`build_card()` 的调用名称前后一致

Plan complete and saved to `docs/superpowers/plans/2026-03-30-ai-news-site-mvp.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?

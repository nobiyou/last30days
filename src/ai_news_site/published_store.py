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

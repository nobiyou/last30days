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
    event_type: str
    summary: str
    key_signal: str
    why_it_matters: str
    who_should_care: str
    topic_tags: list[str]
    source_links: list[str]
    confidence_score: float
    published_at: str

    @property
    def slug(self) -> str:
        return self.canonical_event_id

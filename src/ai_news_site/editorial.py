from .models import CandidateEvent, NewsCard, ResearchFinding
from .topic_router import route_topics


SUMMARY_MAX_LENGTH = 160
SUMMARY_SUFFIX = "。社区讨论集中在这次更新是否会改变近期采用节奏。"


def _trim_summary(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text

    trimmed = text[:limit].rstrip("；。,. ，、 ")
    return trimmed


def build_card(candidate: CandidateEvent, findings: list[ResearchFinding], published_at: str) -> NewsCard:
    top_findings = sorted(findings, key=lambda item: item.score, reverse=True)[:2]
    joined_summary = "；".join(item.summary for item in top_findings if item.summary)
    if joined_summary:
        summary_body = _trim_summary(joined_summary, SUMMARY_MAX_LENGTH - len(SUMMARY_SUFFIX))
        summary = f"{summary_body}{SUMMARY_SUFFIX}" if summary_body else SUMMARY_SUFFIX
    else:
        summary = SUMMARY_SUFFIX

    return NewsCard(
        canonical_event_id=candidate.event_id,
        title=candidate.title,
        summary=summary,
        why_it_matters="这条信号说明相关工具或项目正在获得真实关注，值得尽快验证。",
        who_should_care="独立开发者、创业团队和投资人",
        topic_tags=route_topics(candidate.title, candidate.tags),
        source_links=[item.url for item in top_findings if item.url],
        confidence_score=round(max((item.score for item in top_findings), default=0) / 100, 2),
        published_at=published_at,
    )

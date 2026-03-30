from .models import CandidateEvent, NewsCard, ResearchFinding
from .topic_router import route_topics


SUMMARY_MAX_LENGTH = 160
_GENERIC_SUMMARY_PREFIXES = ("reddit public search", "hn story about", "show hn: ")
_SOURCE_LABELS = {
    "reddit": "Reddit",
    "x": "X",
    "web": "Web",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "hackernews": "HN",
    "bluesky": "Bluesky",
    "truthsocial": "Truth Social",
    "polymarket": "Polymarket",
}


def _trim_summary(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text

    trimmed = text[:limit].rstrip("；。,. ，、”\" ")
    return trimmed


def _pick_signal_text(finding: ResearchFinding) -> str:
    summary = (finding.summary or "").strip()
    lowered = summary.lower()
    if summary and not any(lowered.startswith(prefix) for prefix in _GENERIC_SUMMARY_PREFIXES):
        return summary
    return (finding.title or summary or "相关讨论升温").strip()


def _shorten_signal_text(text: str, limit: int = 40) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip("；。,. ，、”\" ") + "…"


def _derive_event_type(candidate: CandidateEvent, findings: list[ResearchFinding]) -> str:
    combined = " ".join([candidate.title, *(item.title for item in findings)]).lower()
    if any(keyword in combined for keyword in ("funding", "seed", "series", "raises", "raised")):
        return "融资进展"
    if any(keyword in combined for keyword in ("release", "version", "ships", "ship", "launch")):
        return "版本发布"
    if any(keyword in combined for keyword in ("pilot", "warehouse", "deploy", "deployment")):
        return "场景试点"
    if any(keyword in combined for keyword in ("paper", "research", "diffusion", "reinforcement learning")):
        return "研究动态"
    if any(keyword in combined for keyword in ("issue", "roadmap", "request for comments")):
        return "项目动向"
    if any(keyword in combined for keyword in ("show hn", "demo")):
        return "社区热议"
    return "趋势信号"


def _build_summary(candidate: CandidateEvent, findings: list[ResearchFinding]) -> str:
    top_findings = sorted(findings, key=lambda item: item.score, reverse=True)[:2]
    focuses = [_shorten_signal_text(_pick_signal_text(item)) for item in top_findings]
    if len(focuses) >= 2:
        summary = f"最近 7 天，{candidate.title} 的讨论主要集中在“{focuses[0]}”和“{focuses[1]}”。"
    elif focuses:
        summary = f"最近 7 天，{candidate.title} 的讨论主要集中在“{focuses[0]}”。"
    else:
        summary = f"最近 7 天，{candidate.title} 在开发者社区出现了新的关注信号。"
    return _trim_summary(summary, SUMMARY_MAX_LENGTH)


def _build_key_signal(findings: list[ResearchFinding]) -> str:
    usable = [item for item in findings if item.url]
    evidence_count = len(usable) or len(findings)
    source_names = []
    for item in usable or findings:
        label = _SOURCE_LABELS.get(item.source, item.source)
        if label not in source_names:
            source_names.append(label)
    source_count = len(source_names)
    max_score = max((item.score for item in findings), default=0)
    source_text = "、".join(source_names) if source_names else "社区信号"
    return (
        f"{source_count} 个来源、{evidence_count} 条证据，"
        f"最高信号 {max_score:.0f}，当前讨论主要来自 {source_text}。"
    )


def _build_why_it_matters(topic_tags: list[str]) -> str:
    if "Robotics" in topic_tags:
        return "这说明机器人项目正在进入更具体的落地或部署讨论，适合继续跟踪场景验证与商业化进展。"
    if "Agents" in topic_tags and "Open Source" in topic_tags:
        return "这说明智能体与开源工具链正在出现新一轮采用信号，适合尽快评估是否值得试用、接入或持续跟踪。"
    if "Agents" in topic_tags:
        return "这说明智能体工作流和执行框架正在积累真实关注，适合评估是否会影响产品设计和自动化方案。"
    if "Open Source" in topic_tags:
        return "这说明开源生态里出现了值得留意的新工具或新动向，往往意味着更快的试用速度和更低的验证成本。"
    return "这类信号通常比普通热帖更接近真实采用趋势，值得回看原始来源并观察是否持续发酵。"


def _build_who_should_care(topic_tags: list[str]) -> str:
    if "Robotics" in topic_tags:
        return "关注机器人落地、供应链能力和产业机会的团队与投资人"
    if "Agents" in topic_tags and "Open Source" in topic_tags:
        return "正在做 AI 产品、智能体工作流或开发者工具的团队"
    if "Agents" in topic_tags:
        return "正在做智能体产品、流程自动化或 AI 应用编排的团队"
    if "Open Source" in topic_tags:
        return "关注开源生态、开发者工具和基础设施替代机会的人"
    return "独立开发者、创业团队和投资人"


def build_card(candidate: CandidateEvent, findings: list[ResearchFinding], published_at: str) -> NewsCard:
    top_findings = sorted(findings, key=lambda item: item.score, reverse=True)[:2]
    topic_tags = route_topics(candidate.title, candidate.tags)

    return NewsCard(
        canonical_event_id=candidate.event_id,
        title=candidate.title,
        event_type=_derive_event_type(candidate, findings),
        summary=_build_summary(candidate, findings),
        key_signal=_build_key_signal(findings),
        why_it_matters=_build_why_it_matters(topic_tags),
        who_should_care=_build_who_should_care(topic_tags),
        topic_tags=topic_tags,
        source_links=[item.url for item in top_findings if item.url],
        confidence_score=round(max((item.score for item in top_findings), default=0) / 100, 2),
        published_at=published_at,
    )

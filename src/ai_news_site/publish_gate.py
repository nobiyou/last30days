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
    title_lower = candidate.title.lower()
    structural_keywords = ("release", "funding", "launch", "version", "issue", "paper")

    if len(sources) >= 2:
        return PublishDecision(True, "multi_source_confirmation")
    if max_score >= 90:
        return PublishDecision(True, "strong_single_source_breakout")
    if any(keyword in title_lower for keyword in structural_keywords):
        return PublishDecision(True, "structural_update")
    return PublishDecision(False, "insufficient_signal")

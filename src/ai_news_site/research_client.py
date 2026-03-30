import json
import subprocess
import sys
from pathlib import Path

from .models import CandidateEvent, ResearchFinding

_SOURCE_NAMES = (
    "reddit",
    "x",
    "web",
    "youtube",
    "tiktok",
    "instagram",
    "hackernews",
    "bluesky",
    "truthsocial",
    "polymarket",
)


def run_last30days(last30days_root: Path, candidate: CandidateEvent) -> list[ResearchFinding]:
    script = Path(last30days_root) / "scripts" / "last30days.py"
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

    payload = json.loads(result.stdout or "{}")
    findings: list[ResearchFinding] = []

    for source_name in _SOURCE_NAMES:
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

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
    command = [
        sys.executable,
        str(script),
        candidate.query,
        "--emit=json",
        "--quick",
        "--days=7",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        details = stderr.splitlines()[-1] if stderr else str(exc)
        raise RuntimeError(
            f"last30days_failed event_id={candidate.event_id} query={candidate.query} details={details}"
        ) from exc

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

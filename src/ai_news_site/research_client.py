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


def _load_last30days_payload(stdout: str, candidate: CandidateEvent) -> dict:
    output = stdout or "{}"
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        decoder = json.JSONDecoder()
        for index, char in enumerate(output):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(output[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

        preview = output[:200].replace("\n", "\\n")
        raise RuntimeError(
            f"last30days_invalid_json event_id={candidate.event_id} "
            f"query={candidate.query} preview={preview}"
        ) from exc


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

    payload = _load_last30days_payload(result.stdout, candidate)
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

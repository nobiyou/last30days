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

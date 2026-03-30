import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import NewsCard

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def _slugify_topic(topic: str) -> str:
    slug = []
    for ch in topic.lower():
        slug.append(ch if ch.isalnum() else "-")
    return "".join(slug).strip("-")


def _group_cards_by_topic(cards: list[NewsCard]) -> dict[str, list[NewsCard]]:
    grouped: dict[str, list[NewsCard]] = {}
    for card in cards:
        for topic in card.topic_tags:
            grouped.setdefault(topic, []).append(card)
    return grouped


def build_site(output_dir: Path, site_name: str, cards: list[NewsCard]) -> None:
    output_dir = Path(output_dir)
    news_dir = output_dir / "news"
    topics_dir = output_dir / "topics"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    news_dir.mkdir(parents=True, exist_ok=True)
    topics_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    index_html = env.get_template("index.html").render(
        title=f"{site_name} - Latest",
        site_name=site_name,
        cards=cards,
        latest_count=len(cards),
        home_href="index.html",
        css_href="site.css",
        news_href_prefix="",
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    for card in cards:
        detail_html = env.get_template("detail.html").render(
            title=card.title,
            site_name=site_name,
            card=card,
            home_href="../index.html",
            css_href="../site.css",
            news_href_prefix="../",
        )
        (news_dir / f"{card.slug}.html").write_text(detail_html, encoding="utf-8")

    for topic, topic_cards in _group_cards_by_topic(cards).items():
        topic_html = env.get_template("topic.html").render(
            title=f"{topic} - {site_name}",
            site_name=site_name,
            topic_name=topic,
            cards=topic_cards,
            latest_count=len(topic_cards),
            home_href="../index.html",
            css_href="../site.css",
            news_href_prefix="../",
        )
        (topics_dir / f"{_slugify_topic(topic)}.html").write_text(topic_html, encoding="utf-8")

    shutil.copyfile(STATIC_DIR / "site.css", output_dir / "site.css")

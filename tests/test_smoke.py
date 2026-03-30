from ai_news_site.cli import build_parser


def test_build_parser_uses_expected_program_name():
    parser = build_parser()
    assert parser.prog == "ai-news-site"

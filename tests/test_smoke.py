from ai_news_site.cli import build_parser
from ai_news_site.cli import main


def test_build_parser_uses_expected_program_name():
    parser = build_parser()
    assert parser.prog == "ai-news-site"


def test_main_without_subcommand_prints_help_and_returns_non_zero(capsys):
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code != 0
    assert "usage:" in captured.out.lower()

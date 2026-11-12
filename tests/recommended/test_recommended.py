"""RECOMMENDED.md stays consistent: every card has an icon and an install entry, and back.

Run: uv run --with pytest --with pyyaml pytest tests/recommended
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "RECOMMENDED.md").read_text()
CARD = re.compile(r'<a href="https://github\.com/([^/]+/[^/]+)/tree/main/([^"]+)"><img src="\./assets/recommended/([^/]+)/icon\.svg"')


def cards():
    return {name: (source, path) for source, path, name in CARD.findall(PAGE)}


def install():
    block = re.search(r"```yaml\n(.*?)```", PAGE, re.S).group(1)
    return yaml.safe_load(block)["skills"]


def test_cards_and_install_list_match():
    assert sorted(cards()) == sorted(install())


def test_cards_link_to_the_installed_source():
    for name, (source, path) in cards().items():
        entry = install()[name]
        if isinstance(entry, str):
            assert entry == source and path.rsplit("/", 1)[1] == name, name
        else:
            assert entry["source"] == source, name
            assert entry.get("path", path) == path, name


def test_every_card_has_an_icon():
    for name in cards():
        assert (ROOT / "assets" / "recommended" / name / "icon.svg").is_file(), name


def test_readme_points_here():
    assert "./RECOMMENDED.md" in (ROOT / "README.md").read_text()

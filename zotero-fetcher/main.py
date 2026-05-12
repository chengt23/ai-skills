from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(__file__).resolve().parents[0]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from lib import load_settings, run_zotero_fetcher
from lib.runtime import resolve_config_path

DEFAULT_CONFIG_PATH = SKILL_DIR / "config.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch research items from Zotero and write inbox markdown")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--sample-feed", default=None)
    parser.add_argument("--corpus-file", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = resolve_config_path(args.config)
    if config_path is None:
        print(
            "Error: Config file not found. Pass --config or set EVERYTHING_PODCAST_CONFIG / OPENCLAW_PODCAST_CONFIG.",
            file=sys.stderr,
        )
        return 1

    settings = load_settings(
        config_path=config_path,
        root_dir=ROOT,
    )
    settings.ensure_dirs()
    output_path = run_zotero_fetcher(
        settings,
        release_date=date.fromisoformat(args.date),
        dry_run=args.dry_run,
        top_k=args.top_k,
        sample_feed=args.sample_feed,
        corpus_file=args.corpus_file,
    )
    print(f"inbox: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

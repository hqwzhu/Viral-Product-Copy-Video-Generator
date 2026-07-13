#!/usr/bin/env python3
"""Run a pinned MediaCrawler checkout with ENHE's local-browser safety overrides."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Sequence


def apply_creator_override(config: Any, parsed: Any) -> None:
    if getattr(parsed, "platform", "") != "zhihu" or getattr(parsed, "type", "") != "creator":
        return
    creator_ids = [item.strip() for item in str(getattr(parsed, "creator_id", "") or "").split(",") if item.strip()]
    if creator_ids:
        config.ZHIHU_CREATOR_URL_LIST = creator_ids


def patch_safe_cdp_cleanup(config: Any, manager_class: type[Any]) -> None:
    original_cleanup = manager_class.cleanup

    async def safe_cleanup(self: Any, force: bool = False) -> None:
        if getattr(config, "CDP_CONNECT_EXISTING", False):
            self.browser_context = None
            self.browser = None
            return
        await original_cleanup(self, force=force)

    manager_class.cleanup = safe_cleanup


def parse_bootstrap_args(argv: Sequence[str]) -> tuple[Path, list[str]]:
    values = list(argv)
    if "--" not in values:
        raise SystemExit("MediaCrawler bootstrap requires `--` before upstream arguments.")
    separator = values.index("--")
    parser = argparse.ArgumentParser(description="Run a pinned MediaCrawler checkout safely.")
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args(values[:separator])
    checkout = Path(args.checkout).resolve()
    if not (checkout / "main.py").is_file():
        raise SystemExit(f"Pinned MediaCrawler main.py is missing: {checkout}")
    return checkout, values[separator + 1 :]


def main(argv: Sequence[str] | None = None) -> None:
    checkout, upstream_args = parse_bootstrap_args(list(argv) if argv is not None else sys.argv[1:])
    sys.path.insert(0, str(checkout))

    import cmd_arg  # type: ignore[import-not-found]
    import config  # type: ignore[import-not-found]
    from tools.cdp_browser import CDPBrowserManager  # type: ignore[import-not-found]

    patch_safe_cdp_cleanup(config, CDPBrowserManager)
    original_parse_cmd = cmd_arg.parse_cmd

    async def parse_cmd_with_overrides(parsed_argv: Sequence[str] | None = None) -> Any:
        parsed = await original_parse_cmd(upstream_args if parsed_argv is None else parsed_argv)
        apply_creator_override(config, parsed)
        return parsed

    cmd_arg.parse_cmd = parse_cmd_with_overrides

    import main as upstream_main  # type: ignore[import-not-found]

    async def run() -> None:
        try:
            await upstream_main.main()
        finally:
            await upstream_main.async_cleanup()

    asyncio.run(run())


if __name__ == "__main__":
    main()

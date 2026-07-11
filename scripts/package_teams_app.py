#!/usr/bin/env python3
"""Build a sideloadable Microsoft Teams application package."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "teams_app"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id", required=True, help="Microsoft Entra/Azure Bot application ID")
    parser.add_argument(
        "--host",
        required=True,
        help="Public bot host without protocol or path, for example bot.example.com",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "flowmate-teams.zip",
        help="Output zip path (default: dist/flowmate-teams.zip)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    host = args.host.strip().rstrip("/")
    host = re.sub(r"^https?://", "", host, flags=re.IGNORECASE)
    if not host or "/" in host:
        print("error: --host must contain only a public host name", file=sys.stderr)
        return 2

    template = (TEMPLATE_DIR / "manifest.json").read_text(encoding="utf-8")
    manifest_text = template.replace("${MICROSOFT_APP_ID}", args.app_id.strip()).replace(
        "YOUR_PUBLIC_HOST", host
    )
    manifest = json.loads(manifest_text)
    if "${" in manifest_text or "YOUR_PUBLIC_HOST" in manifest_text:
        print("error: unresolved placeholder remains in manifest", file=sys.stderr)
        return 2
    if manifest["id"] != manifest["bots"][0]["botId"]:
        print("error: Teams app ID and bot ID do not match", file=sys.stderr)
        return 2

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = output.parent / "teams-app"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    (stage / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for icon in ("color.png", "outline.png"):
        shutil.copy2(TEMPLATE_DIR / icon, stage / icon)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("manifest.json", "color.png", "outline.png"):
            archive.write(stage / name, arcname=name)

    print(f"Teams package created: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the Chinese documentation site with mkdocs.

Note: versioned deployment (mike) is handled directly in .github/workflows/deploy.yml;
this script covers local build and PDF export only.
"""

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()

# 版本号格式白名单：仅允许语义化版本或 latest（用于 --version 参数校验）
VERSION_PATTERN = re.compile(r'^(latest|v?\d+\.\d+(\.\d+)?(-[a-zA-Z0-9.]+)?)$')


def build_site(clean: bool = False) -> Path:
    """Run mkdocs build and return the site directory."""
    logger.info("Building site with mkdocs%s", " --clean" if clean else "")
    if clean:
        result = subprocess.run(
            ["mkdocs", "build", "--clean", "--strict"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
    if result.returncode != 0:
        logger.error("mkdocs build failed:\n%s", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    site_dir = REPO_ROOT / "site"
    logger.info("Site built at %s", site_dir)
    return site_dir


def export_pdf(site_dir: Path, output_dir: Path) -> bool:
    """Export site pages to PDF (best-effort; requires weasyprint backend)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Exporting PDF from %s to %s", site_dir, output_dir)
    result = subprocess.run(
        ["python3", "-m", "mkdocs_pdf_export"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.warning("PDF export failed (mkdocs-pdf-export may not be installed):\n%s", result.stderr)
        return False
    logger.info("PDF exported to %s", output_dir)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fmt Chinese documentation site")
    parser.add_argument("--version", default="latest",
                        help="Version label for logging/artifact naming (default: latest)")
    parser.add_argument("--clean", action="store_true", help="Clean build")
    parser.add_argument("--pdf", action="store_true", help="Export PDF after build")
    parser.add_argument("--output-dir", default=None, help="PDF output directory")
    args = parser.parse_args()

    if not VERSION_PATTERN.match(args.version):
        parser.error(f"invalid --version: {args.version!r} (expected latest or semver)")

    try:
        site_dir = build_site(clean=args.clean)
        if args.pdf:
            out_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "pdf" / args.version
            export_pdf(site_dir, out_dir)
        logger.info("Build completed (version=%s)", args.version)
    except Exception as e:
        logger.error("Build failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
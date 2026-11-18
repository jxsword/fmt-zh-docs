#!/usr/bin/env python3
"""Rollback translation to a previous version."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
STATE_FILE = REPO_ROOT / ".translation-state.json"


def is_safe_path(base: Path, target: Path) -> bool:
    try:
        return target.resolve().is_relative_to(base.resolve())
    except Exception:
        return False


def get_git_tag(tag_name: str) -> Optional[str]:
    """Get commit hash for a git tag."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', tag_name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def rollback_file(filepath: Path, target_version: str) -> bool:
    """Rollback a single file to a specific version tag."""
    if not is_safe_path(ZH_DIR, filepath):
        logger.error("Unsafe file path: %s", filepath)
        return False
    
    tag_name = f"translation/{filepath.relative_to(ZH_DIR)}/{target_version}"
    commit = get_git_tag(tag_name)
    
    if not commit:
        logger.error("Tag not found: %s", tag_name)
        return False
    
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{filepath.relative_to(REPO_ROOT)}'],
            capture_output=True, text=True, check=True
        )
        filepath.write_text(result.stdout, encoding='utf-8')
        logger.info("Rolled back %s to %s (%s)", filepath.name, target_version, commit[:8])
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to rollback %s: %s", filepath, e)
        return False


def list_versions(filepath: Path) -> list:
    """List available translation versions for a file."""
    if not is_safe_path(ZH_DIR, filepath):
        logger.error("Unsafe file path: %s", filepath)
        return []
    
    prefix = f"translation/{filepath.relative_to(ZH_DIR)}/"
    try:
        result = subprocess.run(
            ['git', 'tag', '-l', f'{prefix}*'],
            capture_output=True, text=True, check=True
        )
        tags = result.stdout.strip().split('\n')
        versions = [t.replace(prefix, '') for t in tags if t]
        return sorted(versions, reverse=True)
    except subprocess.CalledProcessError:
        return []


def main():
    parser = argparse.ArgumentParser(description="Rollback translation to previous version")
    parser.add_argument("--file", required=True, help="File to rollback (e.g., zh/api.md)")
    parser.add_argument("--to-version", help="Target version tag (e.g., v12.1.0)")
    parser.add_argument("--list", action="store_true", help="List available versions for file")
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    if not filepath.exists():
        logger.error("File not found: %s", filepath)
        sys.exit(1)
    
    if not is_safe_path(ZH_DIR, filepath):
        logger.error("File must be under zh/ directory")
        sys.exit(1)
    
    if args.list:
        versions = list_versions(filepath)
        if versions:
            print("Available versions:")
            for v in versions:
                print(f"  {v}")
        else:
            print("No versions found")
        return
    
    if not args.to_version:
        logger.error("--to-version required for file rollback")
        sys.exit(1)
    
    success = rollback_file(filepath, args.to_version)
    
    if success:
        logger.info("Rollback completed successfully")
        sys.exit(0)
    else:
        logger.error("Rollback failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
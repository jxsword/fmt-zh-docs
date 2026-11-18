#!/usr/bin/env python3
"""Validate translation quality for fmt documentation."""

import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
STATE_FILE = REPO_ROOT / ".translation-state.json"
GLOSSARY_FILE = REPO_ROOT / "config" / "glossary.yml"


def load_glossary() -> Dict[str, str]:
    terms = {}
    if not GLOSSARY_FILE.exists():
        return terms
    try:
        import yaml
        with open(GLOSSARY_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        for term in data.get('terms', []):
            en = term.get('en', '')
            zh = term.get('zh', '')
            if en and zh:
                terms[en] = zh
    except Exception as e:
        logger.warning("Failed to load glossary: %s", e)
    return terms


def load_state() -> Dict:
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_code_blocks(content: str) -> List[str]:
    """Extract all code blocks from markdown."""
    pattern = r'```[\s\S]*?```'
    return re.findall(pattern, content)


def extract_inline_code(content: str) -> List[str]:
    """Extract all inline code from markdown."""
    pattern = r'`[^`\n]+`'
    return re.findall(pattern, content)


def extract_html_tags(content: str) -> List[str]:
    """Extract all HTML tags from markdown."""
    pattern = r'<[^>]+>'
    return re.findall(pattern, content)


def extract_urls(content: str) -> List[str]:
    """Extract all URLs from markdown links."""
    pattern = r'\[[^\]]+\]\((https?://[^)]+)\)'
    return re.findall(pattern, content)


def validate_file(source_path: Path, target_path: Path, glossary: Dict[str, str]) -> Dict:
    """Validate a single translated file."""
    errors = []
    warnings = []
    
    if not source_path.exists():
        errors.append(f"Source file not found: {source_path}")
        return {"errors": errors, "warnings": warnings}
    
    if not target_path.exists():
        errors.append(f"Target file not found: {target_path}")
        return {"errors": errors, "warnings": warnings}
    
    source_content = source_path.read_text(encoding='utf-8')
    target_content = target_path.read_text(encoding='utf-8')
    
    # 1. Code block integrity
    source_code_blocks = extract_code_blocks(source_content)
    target_code_blocks = extract_code_blocks(target_content)
    if len(source_code_blocks) != len(target_code_blocks):
        errors.append(f"Code block count mismatch: source={len(source_code_blocks)}, target={len(target_code_blocks)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_code_blocks, target_code_blocks)):
            if src != tgt:
                errors.append(f"Code block {i} modified in translation")
    
    # 2. Inline code integrity
    source_inline = extract_inline_code(source_content)
    target_inline = extract_inline_code(target_content)
    if len(source_inline) != len(target_inline):
        warnings.append(f"Inline code count mismatch: source={len(source_inline)}, target={len(target_inline)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_inline, target_inline)):
            if src != tgt:
                warnings.append(f"Inline code {i} modified: {src} -> {tgt}")
    
    # 3. HTML tag integrity
    source_html = extract_html_tags(source_content)
    target_html = extract_html_tags(target_content)
    if len(source_html) != len(target_html):
        warnings.append(f"HTML tag count mismatch: source={len(source_html)}, target={len(target_html)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_html, target_html)):
            if src != tgt:
                warnings.append(f"HTML tag {i} modified: {src} -> {tgt}")
    
    # 4. URL integrity
    source_urls = extract_urls(source_content)
    target_urls = extract_urls(target_content)
    if len(source_urls) != len(target_urls):
        warnings.append(f"URL count mismatch: source={len(source_urls)}, target={len(target_urls)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_urls, target_urls)):
            if src != tgt:
                warnings.append(f"URL {i} modified: {src} -> {tgt}")
    
    # 5. Glossary terminology consistency
    for en_term, zh_term in glossary.items():
        if en_term in source_content:
            if zh_term not in target_content:
                warnings.append(f"Glossary term '{en_term}' not translated as '{zh_term}'")
    
    # 6. Placeholder check (PROTECTED_* should not remain)
    if 'PROTECTED_' in target_content:
        errors.append("Unrestored PROTECTED_* placeholders found in translation")
    
    # 7. Structure check (heading levels)
    source_headings = re.findall(r'^#{1,6}\s+.+', source_content, re.MULTILINE)
    target_headings = re.findall(r'^#{1,6}\s+.+', target_content, re.MULTILINE)
    if len(source_headings) != len(target_headings):
        warnings.append(f"Heading count mismatch: source={len(source_headings)}, target={len(target_headings)}")
    
    return {"errors": errors, "warnings": warnings}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate translation quality")
    parser.add_argument("--file", default=None,
                        help="只校验指定文件（如 index.md）；缺省校验全部")
    args = parser.parse_args()

    state = load_state()
    glossary = load_glossary()
    logger.info("Loaded %d glossary terms", len(glossary))

    all_errors = []
    all_warnings = []

    targets = state.get('files', {}).keys()
    if args.file:
        if args.file not in state.get('files', {}):
            logger.error("File not in translation state: %s", args.file)
            sys.exit(2)
        targets = [args.file]

    for fname in targets:
        source_path = SOURCE_DIR / fname
        target_path = ZH_DIR / fname
        logger.info("Validating %s", fname)
        result = validate_file(source_path, target_path, glossary)
        for err in result['errors']:
            all_errors.append(f"{fname}: {err}")
        for warn in result['warnings']:
            all_warnings.append(f"{fname}: {warn}")
    
    if all_warnings:
        logger.warning("Warnings (%d):", len(all_warnings))
        for w in all_warnings:
            logger.warning("  %s", w)
    
    if all_errors:
        logger.error("Errors (%d):", len(all_errors))
        for e in all_errors:
            logger.error("  %s", e)
        sys.exit(1)
    else:
        logger.info("All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Fix links and generate anchor mapping for translated documentation."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"


def slugify(text: str) -> str:
    """Generate URL-friendly slug from heading text."""
    # Remove markdown heading markers
    text = re.sub(r'^#+\s*', '', text)
    # Lowercase, replace spaces and special chars
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = text.strip('-')
    return text


def extract_headings(content: str) -> List[Tuple[int, str]]:
    """Extract all headings with their level."""
    headings = []
    for line in content.split('\n'):
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title))
    return headings


def generate_anchor_map(source_dir: Path, target_dir: Path) -> Dict[str, str]:
    """Generate mapping from source heading slugs to target heading slugs."""
    anchor_map = {}
    
    for source_file in source_dir.glob("*.md"):
        target_file = target_dir / source_file.name
        if not target_file.exists():
            continue
        
        source_content = source_file.read_text(encoding='utf-8')
        target_content = target_file.read_text(encoding='utf-8')
        
        source_headings = extract_headings(source_content)
        target_headings = extract_headings(target_content)
        
        if len(source_headings) != len(target_headings):
            logger.warning("Heading count mismatch in %s: source=%d, target=%d", 
                          source_file.name, len(source_headings), len(target_headings))
            continue
        
        for (src_level, src_title), (tgt_level, tgt_title) in zip(source_headings, target_headings):
            if src_level != tgt_level:
                logger.warning("Heading level mismatch: %s vs %s", src_title, tgt_title)
            src_slug = slugify(src_title)
            tgt_slug = slugify(tgt_title)
            if src_slug != tgt_slug:
                anchor_map[src_slug] = tgt_slug
    
    return anchor_map


def fix_relative_links(content: str, anchor_map: Dict[str, str]) -> str:
    """Fix relative .md links and anchor references."""
    # Fix relative .md links: [text](file.md) -> [text](file.md)
    # [text](file.md#anchor) -> [text](file.md#new_anchor)
    def replace_md_link(match):
        text = match.group(1)
        url = match.group(2)
        if url.endswith('.md') or '.md#' in url:
            parts = url.split('#', 1)
            file_part = parts[0]
            if len(parts) > 1:
                anchor = parts[1]
                new_anchor = anchor_map.get(anchor, anchor)
                return f"[{text}]({file_part}#{new_anchor})"
        return match.group(0)
    
    content = re.sub(r'\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)', replace_md_link, content)
    return content


def fix_fmt_dev_links(content: str) -> str:
    """Ensure fmt.dev links are preserved."""
    # fmt.dev links should remain as-is
    # Optionally add ?lang=en for clarity
    return content


def fix_github_links(content: str) -> str:
    """Ensure GitHub source links are preserved."""
    return content


def inject_anchor_ids(content: str, anchor_map: Dict[str, str]) -> str:
    """Inject HTML id attributes into headings for anchor linking."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            slug = slugify(title)
            # Find target slug (reverse lookup)
            target_slug = slug
            for src, tgt in anchor_map.items():
                if tgt == slug:
                    target_slug = src
                    break
            # Add id attribute
            line = f"{'#' * level} {title} {{#{target_slug}}}"
        result.append(line)
    
    return '\n'.join(result)


def process_file(source_path: Path, target_path: Path, anchor_map: Dict[str, str]):
    """Process a single translated file to fix links and inject anchors."""
    content = target_path.read_text(encoding='utf-8')
    
    # Fix relative links
    content = fix_relative_links(content, anchor_map)
    
    # Fix fmt.dev links
    content = fix_fmt_dev_links(content)
    
    # Fix GitHub links
    content = fix_github_links(content)
    
    # Inject anchor IDs
    content = inject_anchor_ids(content, anchor_map)
    
    target_path.write_text(content, encoding='utf-8')
    logger.info("Processed links in %s", target_path.name)


def main():
    anchor_map = generate_anchor_map(SOURCE_DIR, ZH_DIR)
    logger.info("Generated anchor map with %d entries", len(anchor_map))
    
    # Save anchor map
    map_file = REPO_ROOT / "config" / "anchor_map.yml"
    map_file.parent.mkdir(exist_ok=True)
    import yaml
    map_file.write_text(yaml.dump(anchor_map, allow_unicode=True), encoding='utf-8')
    logger.info("Saved anchor map to %s", map_file)
    
    # Process all translated files
    for target_file in ZH_DIR.glob("*.md"):
        process_file(SOURCE_DIR / target_file.name, target_file, anchor_map)
    
    logger.info("Link fixing complete")


if __name__ == "__main__":
    main()
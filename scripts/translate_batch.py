#!/usr/bin/env python3
"""Batch translation engine for fmt documentation."""

import argparse
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
STATE_FILE = REPO_ROOT / ".translation-state.json"
GLOSSARY_FILE = REPO_ROOT / "config" / "glossary.yml"


@dataclass
class Segment:
    id: str
    type: str
    content: str
    hash: str
    file_path: str
    line_start: int
    line_end: int
    metadata: Dict


@dataclass
class PendingTranslation:
    segment: Segment
    source_file: Path
    target_file: Path


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


def save_state(state: Dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def get_pending_translations(state: Dict) -> List[PendingTranslation]:
    pending = []
    # Segment 数据类的合法字段；state 中段落可能带 status/error 等额外键，
    # 直接 **seg_data 展开会在翻译过一次后崩溃（status 键注入）
    known_fields = {"id", "type", "content", "hash", "file_path", "line_start", "line_end", "metadata"}
    for fname, fstate in state.get('files', {}).items():
        source_path = SOURCE_DIR / fname
        target_path = ZH_DIR / fname
        if not source_path.exists():
            continue
        for seg_data in fstate.get('segments', []):
            if seg_data.get('type') == 'code_block':
                continue
            status = seg_data.get('status', 'pending')
            if status == 'pending':
                seg = Segment(**{k: v for k, v in seg_data.items() if k in known_fields})
                pending.append(PendingTranslation(seg, source_path, target_path))
    return pending


def build_prompt(segment: Segment, glossary: Dict[str, str], context: str = "") -> str:
    glossary_text = "\n".join([f"- {en} → {zh}" for en, zh in glossary.items()])
    prompt = f"""Translate the following Markdown segment from English to Chinese.

Glossary (must follow):
{glossary_text}

Context:
{context}

Source text:
{segment.content}

Rules:
1. Keep code blocks, inline code, HTML tags, and URLs unchanged
2. Use glossary terms exactly
3. Professional technical documentation style
4. Output only the translated Markdown, no explanations"""
    return prompt


def translate_segment(segment: Segment, glossary: Dict[str, str], context: str = "") -> str:
    prompt = build_prompt(segment, glossary, context)
    logger.debug("Translating segment %s", segment.id)
    return f"[ZH] {segment.content}"


def write_translated_file(target_path: Path, translated_segments: List[Segment]):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(seg.content for seg in translated_segments)
    target_path.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Batch translate fmt documentation")
    parser.add_argument("--all", action="store_true", help="Translate all pending segments")
    parser.add_argument("--file", help="Translate specific file only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated")
    args = parser.parse_args()

    state = load_state()
    glossary = load_glossary()
    logger.info("Loaded %d glossary terms", len(glossary))

    pending = get_pending_translations(state)
    if args.file:
        pending = [p for p in pending if p.source_file.name == args.file]

    logger.info("Found %d pending translations", len(pending))

    if args.dry_run:
        for p in pending:
            print(f"Would translate: {p.segment.id} from {p.source_file}")
        return

    if not pending:
        logger.info("No pending translations")
        return

    ZH_DIR.mkdir(parents=True, exist_ok=True)

    for i, p in enumerate(pending):
        logger.info("Translating %d/%d: %s", i+1, len(pending), p.segment.id)
        try:
            translated = translate_segment(p.segment, glossary)
            p.segment.content = translated
            p.segment.hash = compute_hash(translated)
            p.segment.metadata['status'] = 'translated'
            p.segment.metadata['translated_at'] = time.time()
        except Exception as e:
            logger.error("Failed to translate %s: %s", p.segment.id, e)
            p.segment.metadata['status'] = 'failed'
            p.segment.metadata['error'] = str(e)

    by_file: Dict[Path, List[Segment]] = {}
    for p in pending:
        by_file.setdefault(p.target_file, []).append(p.segment)

    for target_file, segs in by_file.items():
        write_translated_file(target_file, segs)
        logger.info("Wrote %d segments to %s", len(segs), target_file)

    for fname, fstate in state.get('files', {}).items():
        for seg_data in fstate.get('segments', []):
            for p in pending:
                if p.segment.id == seg_data['id']:
                    seg_data.update({
                        'content': p.segment.content,
                        'hash': p.segment.hash,
                        'status': p.segment.metadata.get('status', 'pending'),
                        'metadata': p.segment.metadata
                    })
                    break

    save_state(state)
    logger.info("Translation complete, state updated")


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


if __name__ == "__main__":
    main()
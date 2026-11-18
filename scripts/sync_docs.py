#!/usr/bin/env python3
"""Sync upstream fmt documentation - minimal version."""

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
STATE_FILE = REPO_ROOT / ".translation-state.json"
UPSTREAM_REPO = "https://github.com/fmtlib/fmt.git"
UPSTREAM_DOC_PATH = "doc"


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
class FileState:
    file_path: str
    upstream_hash: str
    upstream_commit: str
    segments: List[Dict]


@dataclass
class TranslationState:
    upstream_repo: str
    upstream_commit: str
    upstream_version: str
    files: Dict[str, FileState]


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def save_state(state: TranslationState):
    data = {
        'upstream_repo': state.upstream_repo,
        'upstream_commit': state.upstream_commit,
        'upstream_version': state.upstream_version,
        'files': {k: asdict(v) for k, v in state.files.items()}
    }
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info("State saved")


def git_init(cwd: Path):
    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True, text=True)

def git_remote_add_origin(cwd: Path):
    subprocess.run(["git", "remote", "add", "origin", UPSTREAM_REPO], cwd=cwd, check=True, capture_output=True, text=True)

def git_config_sparse(cwd: Path):
    subprocess.run(["git", "config", "core.sparseCheckout", "true"], cwd=cwd, check=True, capture_output=True, text=True)

def write_sparse(target_dir: Path):
    info_dir = target_dir / ".git" / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    (info_dir / "sparse-checkout").write_text(f"{UPSTREAM_DOC_PATH}/*\n")

def git_fetch_main(cwd: Path):
    subprocess.run(["git", "fetch", "--depth=1", "origin", "main"], cwd=cwd, check=True, capture_output=True, text=True)

def git_checkout_fetch_head(cwd: Path):
    subprocess.run(["git", "checkout", "FETCH_HEAD"], cwd=cwd, check=True, capture_output=True, text=True)

def git_rev_parse_head(cwd: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def read_md(doc_dir: Path) -> Dict[str, str]:
    files = {}
    for md_file in doc_dir.iterdir():
        if md_file.suffix != '.md':
            continue
        if not md_file.is_file():
            continue
        files[md_file.name] = md_file.read_text(encoding='utf-8')
    return files


def segment_md(content: str, fname: str) -> List[Segment]:
    segs = []
    lines = content.split('\n')
    i = 0
    sec_idx = 0
    para_idx = 0
    cur_sec = ""
    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st.startswith('```'):
            start = i
            fence = st[:3]
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                i += 1
            if i < len(lines):
                i += 1
            code = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-code-{para_idx}", "code_block", code, compute_hash(code), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st.startswith('|') and '|' in st[1:]:
            start = i
            while i < len(lines) and lines[i].strip().startswith('|'):
                i += 1
            tbl = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-table-{para_idx}", "table", tbl, compute_hash(tbl), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st.startswith('#'):
            level = len(st) - len(st.lstrip('#'))
            title = st.lstrip('#').strip()
            segs.append(Segment(f"{fname}-h{level}-{sec_idx}", "heading", line, compute_hash(line), fname, i+1, i+1, {"level": level, "title": title}))
            cur_sec = title
            sec_idx += 1
            para_idx = 0
            i += 1
            continue
        if st.startswith('![') and '](' in st:
            segs.append(Segment(f"{fname}-img-{para_idx}", "image", line, compute_hash(line), fname, i+1, i+1, {"section": cur_sec}))
            para_idx += 1
            i += 1
            continue
        if st.startswith('<'):
            # HTML 块/跨行注释（<!-- ... --> 可跨多行，'>' 未必在首行）
            start = i
            while i < len(lines) and lines[i].strip() != '':
                i += 1
            html = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-html-{para_idx}", "html_block", html, compute_hash(html), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st:
            start = i
            paras = []
            while i < len(lines) and lines[i].strip() != '':
                ls = lines[i].strip()
                # i > start 才允许 break：首行必被消费，否则残缺行
                # （如 '![unclosed'）会生成空段且该行内容丢失
                if i > start and (ls.startswith('#') or ls.startswith('```') or (ls.startswith('|') and '|' in ls[1:]) or ls.startswith('![') or ls.startswith('<')):
                    break
                paras.append(lines[i])
                i += 1
            p = '\n'.join(paras)
            segs.append(Segment(f"{fname}-p-{para_idx}", "paragraph", p, compute_hash(p), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            if i == start:
                # 防死循环护栏：内层循环未推进时强制前进一行，
                # 否则空 Segment 无限生成会撑爆内存（2026-11-18 OOM 事故根因）
                i += 1
        else:
            i += 1
    return segs


def sync_init() -> Dict:
    logger.info("Initial sync")
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "fmt"
        repo.mkdir()
        git_init(repo)
        git_remote_add_origin(repo)
        git_config_sparse(repo)
        write_sparse(repo)
        git_fetch_main(repo)
        git_checkout_fetch_head(repo)
        sha = git_rev_parse_head(repo)
        doc = repo / UPSTREAM_DOC_PATH
        if not doc.exists():
            raise RuntimeError("No doc dir")
        files = read_md(doc)
        logger.info("Files: %s", list(files.keys()))
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        for fn, ct in files.items():
            (SOURCE_DIR / fn).write_text(ct, encoding='utf-8')
        st = TranslationState(UPSTREAM_REPO, sha, "latest", {})
        for fn, ct in files.items():
            segs = segment_md(ct, fn)
            st.files[fn] = FileState(fn, compute_hash(ct), sha, [asdict(s) for s in segs])
        save_state(st)
        return {"commit": sha, "version": "latest", "files": list(files.keys())}


def main():
    try:
        res = sync_init()
        print(json.dumps(res, ensure_ascii=False))
    except Exception as e:
        logger.error("Failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
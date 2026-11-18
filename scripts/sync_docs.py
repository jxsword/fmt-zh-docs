#!/usr/bin/env python3
"""Sync upstream fmt documentation - full and incremental sync.

CLI:
  --init              全量同步 main 分支
  --tag 12.2.0        全量同步指定版本标签（可单独使用，等价 --init --tag）
  --since <sha>       增量同步：diff since..HEAD，处理 A/M/D/R 变更
  --dry-run           仅检测不写入（source/、state、archive 均不动）
  --repo URL          覆盖上游仓库地址（测试注入本地 file:// 仓库）

变更处理策略：
  A（新增）: 写入 source/，段落全部标记 pending
  M（修改）: 按段落 hash 迁移翻译状态，未变段落保留 translated/reviewed
  D（删除）: source/zh 归档至 archive/，不删翻译历史
  R（重命名）: 旧文件归档，新文件按 hash 迁移段落翻译状态
"""

import argparse
import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
ARCHIVE_DIR = REPO_ROOT / "archive"
STATE_FILE = REPO_ROOT / ".translation-state.json"
UPSTREAM_REPO = "https://github.com/fmtlib/fmt.git"
UPSTREAM_DOC_PATH = "doc"
DEFAULT_REF = "main"

# DR-014（2026-11-19）：历史变更日志不翻译，source/ 保持新鲜但段落全部 skipped，
# 校验器与 CI 翻译跳过这些文件
EXCLUDED_FROM_TRANSLATION = {"ChangeLog-old.md"}

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")

# 段落迁移时随 hash 一并继承的翻译元数据键
MIGRATE_META_KEYS = ("translator", "translated_at", "reviewed_by", "reviewed_at")


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
    excluded: bool = False


@dataclass
class SyncContext:
    """同步目标注入：生产用模块常量，测试注入 tmp_path 隔离目录。"""
    source_dir: Path
    zh_dir: Path
    archive_dir: Path
    state_file: Path
    excluded: frozenset = field(default_factory=lambda: frozenset(EXCLUDED_FROM_TRANSLATION))


@dataclass
class FileChange:
    file: str            # 显示名（R 为 "old -> new"）
    type: str            # A/M/D/R
    added_segments: int = 0
    removed_segments: int = 0
    kept_translated: int = 0
    action: str = ""     # applied / archived / would-apply / would-archive


@dataclass
class TranslationState:
    upstream_repo: str
    upstream_commit: str
    upstream_version: str
    files: Dict[str, FileState]
    archived_files: Dict[str, Dict] = field(default_factory=dict)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def save_state(state_file: Path, state: TranslationState):
    data = {
        'upstream_repo': state.upstream_repo,
        'upstream_commit': state.upstream_commit,
        'upstream_version': state.upstream_version,
        'files': {k: asdict(v) for k, v in state.files.items()},
        'archived_files': state.archived_files,
    }
    state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info("State saved")


def load_state(state_file: Path) -> TranslationState:
    """从 JSON 载入；旧格式与额外键（如 excluded_reason）向后兼容。"""
    data = json.loads(state_file.read_text(encoding='utf-8'))
    files = {k: _fstate_from_dict(v) for k, v in data.get('files', {}).items()}
    return TranslationState(
        upstream_repo=data.get('upstream_repo', ''),
        upstream_commit=data.get('upstream_commit', ''),
        upstream_version=data.get('upstream_version', 'latest'),
        files=files,
        archived_files=data.get('archived_files', {}),
    )


# ---------- git 帮助函数（subprocess 一律内联参数列表，不用 shell 拼接） ----------

def _git(args: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True,
                            capture_output=True, text=True)
    return result.stdout


def _safe_join(base: Path, rel: str) -> Path:
    """resolve 后校验仍位于 base 内，防路径逃逸。"""
    base = base.resolve()
    p = (base / rel).resolve()
    if not p.is_relative_to(base):
        raise ValueError(f"path escapes {base}: {rel}")
    return p


def prepare_upstream(repo_url: str, workdir: Path, ref: str) -> str:
    """blobless + sparse clone 上游并 checkout 指定 ref，返回 HEAD SHA。

    blobless clone 保留完整提交/树历史（diff since..HEAD 必需），blob 按需取
    （sparse-checkout 仅 doc/）。"""
    workdir.mkdir(parents=True)
    _git(["clone", "--filter=blob:none", "--no-checkout", "--sparse",
          repo_url, str(workdir)])
    _git(["sparse-checkout", "set", UPSTREAM_DOC_PATH], cwd=workdir)
    if ref != DEFAULT_REF:
        # 显式写回 refs/tags/，否则仅存于 FETCH_HEAD，checkout 无法解析
        _git(["fetch", "--no-tags", "origin",
              f"refs/tags/{ref}:refs/tags/{ref}"], cwd=workdir)
    _git(["checkout", ref], cwd=workdir)
    return _git(["rev-parse", "HEAD"], cwd=workdir).strip()


def parse_name_status(raw: str) -> List[Tuple[str, str, str]]:
    """解析 git diff --name-status 输出为 (type, old, new) 列表。

    R/C 行形如 "R100\\told\\tnew"，其余为 "M\\tpath"。"""
    out = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            logger.warning("Skipping unparsable diff line: %r", line)
            continue
        code = parts[0]
        t = code[0]
        if t in ('R', 'C'):
            if len(parts) < 3:
                logger.warning("Rename/copy line missing paths: %r", line)
                continue
            out.append((t, parts[1], parts[2]))
        else:
            out.append((t, parts[1], parts[1]))
    return out


def read_md(doc_dir: Path) -> Dict[str, str]:
    files = {}
    for md_file in sorted(doc_dir.iterdir()):
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


# ---------- 段落状态迁移 ----------

def migrate_segment_dicts(new_segs: List[Segment],
                          old_segments: List[Dict],
                          excluded: bool) -> Tuple[List[Dict], int, int, int]:
    """按 hash 迁移旧段落翻译状态到新分段结果。

    返回 (新段落 dict 列表, added, removed, kept_translated)。
    未命中旧 hash 的段落标记 pending（excluded 文件一律 skipped）；
    非 excluded 文件继承到 skipped 状态时降级为 pending（排除集可能已变化）。"""
    old_by_hash = {s['hash']: s for s in old_segments}
    out = []
    added = 0
    kept = 0
    for seg in new_segs:
        d = asdict(seg)
        old = old_by_hash.get(seg.hash)
        if excluded:
            d['status'] = 'skipped'
        elif old:
            status = old.get('status') or 'pending'
            if status == 'skipped':
                status = 'pending'
            d['status'] = status
            old_meta = old.get('metadata', {})
            for k in MIGRATE_META_KEYS:
                if k in old_meta:
                    d['metadata'][k] = old_meta[k]
            if d['status'] in ('translated', 'reviewed'):
                kept += 1
        else:
            d['status'] = 'pending'
            added += 1
        out.append(d)
    removed = len({s['hash'] for s in old_segments} - {seg.hash for seg in new_segs})
    return out, added, removed, kept


def _archive_file(ctx: SyncContext, fname: str) -> int:
    """把 source/zh 中的文件移入 archive/（归档不删翻译历史）。"""
    moved = 0
    for root, sub in ((ctx.source_dir, "source"), (ctx.zh_dir, "zh")):
        f = root / fname
        if f.exists():
            dest_dir = _safe_join(ctx.archive_dir / sub, ".")
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(dest_dir / fname))
            moved += 1
    return moved


def _read_upstream_doc(repo_dir: Path, rel_path: str) -> str:
    """读取上游工作树 doc/ 下文件；路径逃逸或超出 doc/ 抛错。"""
    p = _safe_join(repo_dir, rel_path)
    doc_root = (repo_dir / UPSTREAM_DOC_PATH).resolve()
    if not p.is_relative_to(doc_root):
        raise ValueError(f"refusing to read outside {UPSTREAM_DOC_PATH}/: {rel_path}")
    if not p.is_file():
        raise FileNotFoundError(f"upstream doc not found after checkout: {rel_path}")
    return p.read_text(encoding='utf-8')


_FSTATE_FIELDS = {"file_path", "upstream_hash", "upstream_commit", "segments", "excluded"}


def _fstate_from_dict(d: Dict) -> FileState:
    """从（可能是 archived_files 里的）dict 重建 FileState，容忍额外键。"""
    known = {k: v for k, v in d.items() if k in _FSTATE_FIELDS}
    known.setdefault('excluded', False)
    return FileState(**known)


def _archive_state_entry(state: TranslationState, fname: str, head_sha: str):
    """把 state.files 中的条目移入 archived_files（幂等：不存在则跳过）。"""
    fstate = state.files.get(fname)
    if fstate is None:
        return
    d = asdict(fstate)
    d['archived_at'] = time.strftime("%Y-%m-%d")
    d['upstream_commit_at_archive'] = head_sha
    state.archived_files[fname] = d
    del state.files[fname]


def _apply_change(ctx: SyncContext, state: TranslationState, repo_dir: Path,
                  t: str, old_path: str, new_path: str,
                  head_sha: str, dry_run: bool) -> FileChange:
    """应用单个上游文件变更到 source/、archive/ 与 state。

    幂等性：同一变更重复应用（CI 重跑）不重复归档、不重置已迁移状态。"""
    new_fname = Path(new_path).name if new_path else Path(old_path).name

    # D：归档 source/zh 与 state 条目，不删翻译历史
    if t == 'D':
        old_fname = Path(old_path).name
        action = "would-archive" if dry_run else "archived"
        if not dry_run:
            _archive_file(ctx, old_fname)  # 文件已在 archive 时为 no-op
            _archive_state_entry(state, old_fname, head_sha)
        return FileChange(old_fname, 'D', action=action)

    # A/M/R：读取上游新内容，按需迁移旧段落状态
    content = _read_upstream_doc(repo_dir, new_path)
    old_fstate: Optional[FileState] = None
    display = new_fname
    if t == 'R':
        old_fname = Path(old_path).name
        display = f"{old_fname} -> {new_fname}"
        old_fstate = state.files.get(old_fname)
        from_archived = False
        if old_fstate is None and old_fname in state.archived_files:
            # 重跑场景：旧条目已归档，从归档恢复以迁移状态
            old_fstate = _fstate_from_dict(state.archived_files[old_fname])
            from_archived = True
        if not dry_run:
            _archive_file(ctx, old_fname)
            if not from_archived:
                _archive_state_entry(state, old_fname, head_sha)
    else:
        # A/M：state 已有条目（重跑场景）时按 hash 迁移，避免重置翻译状态
        old_fstate = state.files.get(new_fname)
        if old_fstate is None and t == 'M':
            logger.warning("M on unknown file %s, treating as A", new_fname)

    is_excluded = new_fname in ctx.excluded
    old_segments = old_fstate.segments if old_fstate is not None else []
    segs = segment_md(content, new_fname)
    seg_dicts, added, removed, kept = migrate_segment_dicts(segs, old_segments, is_excluded)
    fstate = FileState(
        file_path=new_fname,
        upstream_hash=compute_hash(content),
        upstream_commit=head_sha,
        segments=seg_dicts,
        excluded=is_excluded,
    )
    action = "would-apply" if dry_run else "applied"
    if not dry_run:
        out = _safe_join(ctx.source_dir, new_fname)
        out.write_text(content, encoding='utf-8')
        state.files[new_fname] = fstate
    return FileChange(display, t if t != 'C' else 'A',
                      added_segments=added, removed_segments=removed,
                      kept_translated=kept, action=action)


def sync_init(ctx: SyncContext, repo_url: str, tag: Optional[str] = None,
              dry_run: bool = False) -> Dict:
    """全量同步：拉取 ref（main 或 tag）的 doc/ 到 source/ 并重建 state。"""
    ref = tag or DEFAULT_REF
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "fmt"
        sha = prepare_upstream(repo_url, repo, ref)
        doc = repo / UPSTREAM_DOC_PATH
        if not doc.exists():
            raise RuntimeError(f"No doc dir after checkout of {ref}")
        files = read_md(doc)
        logger.info("Files: %s", list(files.keys()))
        if not dry_run:
            ctx.source_dir.mkdir(parents=True, exist_ok=True)
            for fn, ct in files.items():
                (_safe_join(ctx.source_dir, fn)).write_text(ct, encoding='utf-8')
            st = TranslationState(repo_url, sha, tag or "latest", {})
            for fn, ct in files.items():
                is_excluded = fn in ctx.excluded
                segs = segment_md(ct, fn)
                seg_dicts = []
                for s in segs:
                    d = asdict(s)
                    d['status'] = 'skipped' if is_excluded else 'pending'
                    seg_dicts.append(d)
                st.files[fn] = FileState(fn, compute_hash(ct), sha, seg_dicts, excluded=is_excluded)
            save_state(ctx.state_file, st)
        return {
            "mode": "init",
            "ref": ref,
            "commit": sha,
            "version": tag or "latest",
            "dry_run": dry_run,
            "has_changes": bool(files),
            "files": sorted(files.keys()),
        }


def sync_since(ctx: SyncContext, repo_url: str, since_sha: str,
               tag: Optional[str] = None, dry_run: bool = False) -> Dict:
    """增量同步：diff since..HEAD，应用 A/M/D/R 变更到 source/state/archive。"""
    if not SHA40_RE.match(since_sha):
        raise ValueError(f"--since expects 40-hex sha, got: {since_sha!r}")
    ref = tag or DEFAULT_REF
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "fmt"
        sha = prepare_upstream(repo_url, repo, ref)
        # 校验 since 在拉取的历史内（不在则报错，避免静默漏检）
        _git(["cat-file", "-e", f"{since_sha}^{{commit}}"], cwd=repo)
        raw = _git(["diff", "--name-status", f"{since_sha}..{sha}"], cwd=repo)
        triples = parse_name_status(raw)
        if not triples:
            logger.info("No changes between %s..%s", since_sha[:8], sha[:8])
            return {"mode": "incremental", "ref": ref, "commit": sha,
                    "version": tag or "latest", "dry_run": dry_run,
                    "has_changes": False, "changes": []}
        state = load_state(ctx.state_file)  # 增量必须基于既有 state
        changes: List[FileChange] = []
        for t, old, new in triples:
            # 只关心 doc/ 下的 markdown；其他路径记录跳过
            target = new if t != 'D' else old
            if not target.startswith(f"{UPSTREAM_DOC_PATH}/") or not target.endswith('.md'):
                logger.info("Skipping non-doc markdown change: %s %s -> %s", t, old, new)
                continue
            changes.append(_apply_change(ctx, state, repo, t, old, new, sha, dry_run))
        state.upstream_commit = sha
        state.upstream_version = tag or "latest"
        if not dry_run:
            save_state(ctx.state_file, state)
        return {
            "mode": "incremental",
            "ref": ref,
            "commit": sha,
            "version": tag or "latest",
            "dry_run": dry_run,
            "has_changes": bool(changes),
            "changes": [asdict(c) for c in changes],
        }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sync_docs.py",
        description="同步上游 fmt 文档（全量 --init/--tag + 增量 --since）")
    p.add_argument("--init", action="store_true", help="全量同步（main 或 --tag 指定版本）")
    p.add_argument("--tag", metavar="TAG",
                   help="上游版本标签，MAJOR.MINOR.PATCH 格式（如 12.2.0）")
    p.add_argument("--since", metavar="SHA",
                   help="增量同步起点 commit SHA（40 位十六进制）")
    p.add_argument("--dry-run", action="store_true",
                   help="仅检测变更不写入（不更新 source/、state、archive/）")
    p.add_argument("--repo", default=UPSTREAM_REPO,
                   help="上游仓库 URL（默认 https://github.com/fmtlib/fmt.git；测试可注入本地 file:// 仓库）")
    return p


def main(argv: Optional[List[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.tag and not SEMVER_RE.match(args.tag):
        parser.error("--tag 需为 MAJOR.MINOR.PATCH 语义化版本格式（如 12.2.0）")
    if args.since and not SHA40_RE.match(args.since):
        parser.error("--since 需为 40 位十六进制 commit SHA")
    if args.init and args.since:
        parser.error("--init 与 --since 互斥")
    if not (args.init or args.tag or args.since):
        parser.error("需指定模式：--init（全量）/ --tag（全量到指定版本）/ --since（增量）")

    ctx = SyncContext(SOURCE_DIR, ZH_DIR, ARCHIVE_DIR, STATE_FILE)
    try:
        if args.since:
            res = sync_since(ctx, args.repo, args.since,
                             tag=args.tag, dry_run=args.dry_run)
        else:
            res = sync_init(ctx, args.repo, tag=args.tag, dry_run=args.dry_run)
        print(json.dumps(res, ensure_ascii=False))
    except Exception as e:
        logger.error("Failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

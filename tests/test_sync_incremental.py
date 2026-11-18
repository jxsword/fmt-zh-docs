"""sync_docs.py 增量同步测试。

用本地临时 git 仓库（file:// URL）模拟上游，覆盖：
  - CLI 参数校验（--tag 语义化版本 / --since 40 位十六进制 / 模式互斥）
  - git diff --name-status 解析（A/M/D/R）
  - 全量同步（--init / --tag）
  - 增量同步 A/M/D/R 全变更类型 + 段落翻译状态按 hash 迁移 + 归档不删历史
  - --dry-run 零写入
  - 幂等性（同一变更重复应用不重置状态）

Mimosa 纪律：subprocess 一律内联参数列表；路径 pathlib resolve 校验。
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import sync_docs  # noqa: E402
from sync_docs import (  # noqa: E402
    SyncContext,
    parse_name_status,
    sync_init,
    sync_since,
)


# ---------- 工具 ----------

def git(*args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   capture_output=True, text=True)


def rev_head(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                          check=True, capture_output=True, text=True).stdout.strip()


def tree_hash(root: Path) -> str:
    """目录树内容指纹（dry-run 零写入断言用）。"""
    h = hashlib.sha256()
    if not root.exists():
        return "missing"
    for p in sorted(root.rglob("*")):
        h.update(str(p.relative_to(root)).encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


@pytest.fixture
def upstream(tmp_path) -> Path:
    """本地"上游"仓库：doc/ 下 api.md、guide.md、legacy.md 三个文件。"""
    repo = tmp_path / "upstream"
    (repo / "doc").mkdir(parents=True)
    git("init", "-b", "main", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test Upstream", cwd=repo)
    (repo / "doc" / "api.md").write_text("# API\n\npara one\n\npara two\n", encoding="utf-8")
    (repo / "doc" / "guide.md").write_text("# Guide\n\nintro text\n\nmore text\n", encoding="utf-8")
    (repo / "doc" / "legacy.md").write_text("# Legacy\n\nold stuff\n", encoding="utf-8")
    git("add", ".", cwd=repo)
    git("commit", "-m", "c0: initial docs", cwd=repo)
    return repo


def make_ctx(tmp_path, excluded=frozenset({"legacy.md"})) -> SyncContext:
    return SyncContext(
        source_dir=tmp_path / "source",
        zh_dir=tmp_path / "zh",
        archive_dir=tmp_path / "archive",
        state_file=tmp_path / ".translation-state.json",
        excluded=excluded,
    )


def mark_all_translated(ctx: SyncContext, fname: str):
    """把 state 中指定文件全部段落标记为 translated（模拟 M2 已翻译完）。"""
    state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
    for seg in state["files"][fname]["segments"]:
        seg["status"] = "translated"
        seg["metadata"]["translator"] = "test-agent"
        seg["metadata"]["translated_at"] = "2026-11-19"
    ctx.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- CLI 参数校验 ----------

class TestArgumentValidation:
    def _fake_sync(self, monkeypatch):
        calls = {}

        def fake_init(ctx, repo_url, tag=None, dry_run=False):
            calls["mode"] = "init"
            calls["tag"] = tag
            return {"mode": "init"}

        def fake_since(ctx, repo_url, since, tag=None, dry_run=False):
            calls["mode"] = "since"
            calls["since"] = since
            return {"mode": "incremental"}

        monkeypatch.setattr(sync_docs, "sync_init", fake_init)
        monkeypatch.setattr(sync_docs, "sync_since", fake_since)
        return calls

    def test_tag_rejects_non_semver(self, monkeypatch):
        self._fake_sync(monkeypatch)
        for bad in ("v12.2.0", "12.2", "12", "abc", "12.2.0-rc1"):
            with pytest.raises(SystemExit) as e:
                sync_docs.main(["--tag", bad])
            assert e.value.code == 2, f"{bad} should be rejected"

    def test_tag_accepts_semver(self, monkeypatch):
        calls = self._fake_sync(monkeypatch)
        sync_docs.main(["--tag", "12.2.0"])
        assert calls["mode"] == "init" and calls["tag"] == "12.2.0"

    def test_since_rejects_non_40hex(self, monkeypatch):
        self._fake_sync(monkeypatch)
        for bad in ("abc123", "14ac0d5a", "z" * 40, "12345"):
            with pytest.raises(SystemExit) as e:
                sync_docs.main(["--since", bad])
            assert e.value.code == 2, f"{bad} should be rejected"

    def test_since_accepts_40hex(self, monkeypatch):
        calls = self._fake_sync(monkeypatch)
        sha = "a" * 40
        sync_docs.main(["--since", sha])
        assert calls["mode"] == "since" and calls["since"] == sha

    def test_init_and_since_mutually_exclusive(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit) as e:
            sync_docs.main(["--init", "--since", "a" * 40])
        assert e.value.code == 2

    def test_requires_mode_flag(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit) as e:
            sync_docs.main([])
        assert e.value.code == 2

    def test_no_mode_but_dry_run_alone_rejected(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit):
            sync_docs.main(["--dry-run"])


# ---------- diff 解析 ----------

class TestParseNameStatus:
    def test_simple_types(self):
        raw = "A\tdoc/new.md\nM\tdoc/api.md\nD\tdoc/old.md\n"
        out = parse_name_status(raw)
        assert out == [("A", "doc/new.md", "doc/new.md"),
                       ("M", "doc/api.md", "doc/api.md"),
                       ("D", "doc/old.md", "doc/old.md")]

    def test_rename_with_score(self):
        raw = "R100\tdoc/guide.md\tdoc/manual.md\n"
        assert parse_name_status(raw) == [("R", "doc/guide.md", "doc/manual.md")]

    def test_copy_parsed_as_R_prefix(self):
        raw = "C90\tdoc/a.md\tdoc/b.md\n"
        assert parse_name_status(raw) == [("C", "doc/a.md", "doc/b.md")]

    def test_empty_and_garbage_lines(self):
        assert parse_name_status("") == []
        assert parse_name_status("\n\n") == []
        # 无制表符的行被跳过且不抛错
        assert parse_name_status("garbage line") == []


# ---------- 全量同步 ----------

class TestSyncInit:
    def test_init_from_local_upstream(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}")
        assert res["mode"] == "init"
        assert res["ref"] == "main"
        assert res["has_changes"] is True
        assert sorted(res["files"]) == ["api.md", "guide.md", "legacy.md"]
        assert (tmp_path / "source" / "api.md").read_text(encoding="utf-8").startswith("# API")
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert set(state["files"].keys()) == {"api.md", "guide.md", "legacy.md"}
        # 非 excluded 文件段落 pending，excluded（legacy.md）段落 skipped
        assert state["files"]["api.md"]["segments"][0]["status"] == "pending"
        assert all(s["status"] == "skipped" for s in state["files"]["legacy.md"]["segments"])
        assert state["files"]["legacy.md"]["excluded"] is True
        assert len(state["upstream_commit"]) == 40

    def test_init_dry_run_writes_nothing(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}", dry_run=True)
        assert res["dry_run"] is True
        assert not (tmp_path / "source").exists()
        assert not ctx.state_file.exists()

    def test_init_from_tag(self, tmp_path, upstream):
        git("tag", "1.2.3", cwd=upstream)
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}", tag="1.2.3")
        assert res["ref"] == "1.2.3" and res["version"] == "1.2.3"
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert state["upstream_version"] == "1.2.3"

    def test_init_rejects_nonexistent_tag(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        with pytest.raises(subprocess.CalledProcessError):
            sync_init(ctx, f"file://{upstream}", tag="9.9.9")


# ---------- 增量同步 ----------

class TestSyncSince:
    def _init_and_mark(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}")
        mark_all_translated(ctx, "api.md")
        mark_all_translated(ctx, "guide.md")
        return ctx, rev_head(upstream)

    def test_full_cycle_MARD(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        zh_dir = tmp_path / "zh"
        zh_dir.mkdir()
        (zh_dir / "guide.md").write_text("# 指南（翻译历史）\n", encoding="utf-8")

        # 上游三连提交：M 改 api.md 一段；A 加 new.md；R 改名 guide→manual；D 删 legacy
        (upstream / "doc" / "api.md").write_text(
            "# API\n\npara one CHANGED\n\npara two\n", encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c1: modify api", cwd=upstream)
        (upstream / "doc" / "new.md").write_text("# New\n\nbrand new\n", encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c2: add new", cwd=upstream)
        git("mv", "doc/guide.md", "doc/manual.md", cwd=upstream)
        git("rm", "doc/legacy.md", cwd=upstream)
        git("commit", "-m", "c3: rename and delete", cwd=upstream)

        res = sync_since(ctx, f"file://{upstream}", sha0)
        assert res["mode"] == "incremental" and res["has_changes"] is True
        by_file = {c["file"]: c for c in res["changes"]}
        # rename 变更的 file 字段为 "old -> new" 展示名
        assert set(by_file.keys()) == {"api.md", "new.md", "guide.md -> manual.md", "legacy.md"}
        assert by_file["api.md"]["type"] == "M"
        assert by_file["new.md"]["type"] == "A"
        assert by_file["legacy.md"]["type"] == "D"
        # rename 的 file 字段为 "old -> new" 展示名，type 为 R
        rename = next(c for c in res["changes"] if c["type"] == "R")
        assert rename["file"] == "guide.md -> manual.md"

        # source/：新文件在、删除的不在
        assert (tmp_path / "source" / "new.md").exists()
        assert (tmp_path / "source" / "manual.md").exists()
        assert not (tmp_path / "source" / "guide.md").exists()
        assert not (tmp_path / "source" / "legacy.md").exists()
        # 归档不删翻译历史
        assert (tmp_path / "archive" / "source" / "guide.md").exists()
        assert (tmp_path / "archive" / "source" / "legacy.md").exists()
        assert (tmp_path / "archive" / "zh" / "guide.md").read_text(
            encoding="utf-8").startswith("# 指南")

        # state：归档条目与新条目
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert set(state["files"].keys()) == {"api.md", "new.md", "manual.md"}
        assert set(state["archived_files"].keys()) == {"guide.md", "legacy.md"}
        assert state["archived_files"]["guide.md"]["archived_at"] == "2026-11-19"

        # api.md 段落迁移：仅被改写的一段 pending，其余保持 translated + 元数据
        api = {s["content"]: s for s in state["files"]["api.md"]["segments"]}
        changed = api["para one CHANGED"]
        assert changed["status"] == "pending"
        assert changed["content"] == "para one CHANGED"
        for content in ("# API", "para two"):
            seg = api[content]
            assert seg["status"] == "translated"
            assert seg["metadata"]["translator"] == "test-agent"
        # M 摘要统计
        assert by_file["api.md"]["added_segments"] == 1
        assert by_file["api.md"]["kept_translated"] == 2

        # manual.md（原 guide.md）状态按 hash 迁移
        manual = state["files"]["manual.md"]
        assert all(s["status"] == "translated" for s in manual["segments"])
        assert manual["segments"][0]["metadata"]["translator"] == "test-agent"

        # upstream commit 前进
        assert state["upstream_commit"] == rev_head(upstream)

    def test_dry_run_writes_nothing(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        (upstream / "doc" / "api.md").write_text("# API\n\npara one EDITED\n\npara two\n",
                                                 encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c1", cwd=upstream)

        snap = {d: tree_hash(d) for d in (tmp_path / "source", tmp_path / "zh",
                                          tmp_path / "archive", ctx.state_file)}
        res = sync_since(ctx, f"file://{upstream}", sha0, dry_run=True)
        assert res["dry_run"] is True and res["has_changes"] is True
        assert res["changes"][0]["action"] == "would-apply"
        for d, h in snap.items():
            assert tree_hash(d) == h, f"dry-run wrote to {d}"

    def test_no_changes_when_since_is_head(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        res = sync_since(ctx, f"file://{upstream}", sha0)
        assert res["has_changes"] is False and res["changes"] == []

    def test_rerun_same_since_is_idempotent(self, tmp_path, upstream):
        """CI 重跑：同一 since 重复应用不得重置已迁移的翻译状态。"""
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        git("mv", "doc/guide.md", "doc/manual.md", cwd=upstream)
        git("commit", "-m", "rename", cwd=upstream)
        sync_since(ctx, f"file://{upstream}", sha0)
        state1 = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert all(s["status"] == "translated"
                   for s in state1["files"]["manual.md"]["segments"])
        # 第二次运行（模拟失败重试）
        sync_since(ctx, f"file://{upstream}", sha0)
        state2 = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert all(s["status"] == "translated"
                   for s in state2["files"]["manual.md"]["segments"])
        # legacy.md 仍在上游且未被本批变更触及，保留在 files 中
        assert set(state2["files"].keys()) == {"api.md", "manual.md", "legacy.md"}
        # api.md 未变更，状态不因重跑翻转
        api_statuses = {s["status"] for s in state2["files"]["api.md"]["segments"]}
        assert api_statuses == {"translated"}

    def test_since_unknown_sha_fails_cleanly(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}")
        bogus = "f" * 40
        with pytest.raises(subprocess.CalledProcessError):
            sync_since(ctx, f"file://{upstream}", bogus)

    def test_non_doc_changes_ignored(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        (upstream / "README.md").write_text("# upstream readme\n", encoding="utf-8")
        (upstream / "doc" / "api.md").write_text("# API\n\npara one\n\npara two NEW\n",
                                                 encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "mixed change", cwd=upstream)
        res = sync_since(ctx, f"file://{upstream}", sha0)
        files_touched = {c["file"] for c in res["changes"]}
        assert "api.md" in files_touched
        assert all(f.endswith(".md") and f not in ("README.md",) for f in files_touched)

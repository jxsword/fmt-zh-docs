"""M4 脚本测试：build_site / fix_links / rollback_translation / validate_code_examples。

subprocess 一律 monkeypatch，不真实编译/构建；文件操作在 tmp_path 隔离。
目标：scripts 总体覆盖率从 48% 提升至 ≥80%（M4 质量专项）。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_site as bs  # noqa: E402
import fix_links as fl  # noqa: E402
import rollback_translation as rb  # noqa: E402
import validate_code_examples as vc  # noqa: E402


# ---------- fix_links ----------

class TestFixLinks:
    def test_slugify_basic(self):
        assert fl.slugify("Compile-Time Checks") == "compile-time-checks"
        assert fl.slugify("## Format API") == "format-api"
        assert fl.slugify("Fill and  alignment!") == "fill-and-alignment"
        assert fl.slugify("---") == ""

    def test_extract_headings(self):
        content = "# T1\n\ntext\n\n### T2 with `code`\n\ntext\n"
        assert fl.extract_headings(content) == [(1, "T1"), (3, "T2 with `code`")]
        assert fl.extract_headings("") == []

    def test_generate_anchor_map(self, tmp_path):
        src = tmp_path / "src"
        tgt = tmp_path / "tgt"
        src.mkdir()
        tgt.mkdir()
        (src / "a.md").write_text("# Core API\n\n## Compile-Time Checks\n", encoding="utf-8")
        (tgt / "a.md").write_text("# 核心 API\n\n## 编译时检查\n", encoding="utf-8")
        m = fl.generate_anchor_map(src, tgt)
        assert m == {"core-api": "核心-api", "compile-time-checks": "编译时检查"}
        # 标题数不一致时跳过该文件
        (src / "b.md").write_text("# One\n\n# Two\n", encoding="utf-8")
        (tgt / "b.md").write_text("# 只有一个\n", encoding="utf-8")
        m2 = fl.generate_anchor_map(src, tgt)
        assert "one" not in m2

    def test_fix_relative_links(self):
        amap = {"compile-time-checks": "编译时检查"}
        content = "[see](api.md#compile-time-checks) and [x](api.md) and [y](other.md#absent)"
        out = fl.fix_relative_links(content, amap)
        assert "api.md#编译时检查" in out
        assert "[x](api.md)" in out
        assert "other.md#absent" in out  # 未知锚点原样保留

    def test_identity_link_fixers(self):
        assert fl.fix_fmt_dev_links("[f](https://fmt.dev/x)") == "[f](https://fmt.dev/x)"
        assert fl.fix_github_links("[g](https://github.com/a)") == "[g](https://github.com/a)"

    def test_inject_anchor_ids(self):
        amap = {"compile-time-checks": "编译时检查"}
        content = "## 编译时检查\n\n正文\n"
        out = fl.inject_anchor_ids(content, amap)
        assert "## 编译时检查 {#compile-time-checks}" in out
        # 无映射命中的标题保持 slug 原样
        out2 = fl.inject_anchor_ids("## 独立标题\n", {})
        assert "{#独立标题}" in out2


# ---------- build_site ----------

class TestBuildSite:
    def _ok_run(self, args, **kw):
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    def _fail_run(self, args, **kw):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="boom")

    def test_build_site_success(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(bs.subprocess, "run", self._ok_run)
        site = bs.build_site()
        assert site == tmp_path / "site"

    def test_build_site_clean_flag(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        seen = {}
        def spy(args, **kw):
            seen["args"] = args
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        monkeypatch.setattr(bs.subprocess, "run", spy)
        bs.build_site(clean=True)
        assert "--clean" in seen["args"] and "--strict" in seen["args"]

    def test_build_site_failure_raises(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(bs.subprocess, "run", self._fail_run)
        with pytest.raises(subprocess.CalledProcessError):
            bs.build_site()

    def test_export_pdf_failure_returns_false(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(bs.subprocess, "run", self._fail_run)
        assert bs.export_pdf(tmp_path / "site", tmp_path / "pdf") is False

    def test_export_pdf_success_creates_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(bs.subprocess, "run", self._ok_run)
        out = tmp_path / "pdf"
        assert bs.export_pdf(tmp_path / "site", out) is True
        assert out.exists()


# ---------- rollback_translation ----------

class TestRollback:
    def test_is_safe_path(self, tmp_path):
        inside = tmp_path / "zh" / "api.md"
        assert rb.is_safe_path(tmp_path, inside) is True
        assert rb.is_safe_path(tmp_path, Path("/etc/passwd")) is False

    def test_get_git_tag_found_and_missing(self, monkeypatch):
        monkeypatch.setattr(rb.subprocess, "run",
                            lambda a, **k: subprocess.CompletedProcess(a, 0, stdout="abc123\n", stderr=""))
        assert rb.get_git_tag("t1") == "abc123"
        def fail(a, **k):
            raise subprocess.CalledProcessError(1, a)
        monkeypatch.setattr(rb.subprocess, "run", fail)
        assert rb.get_git_tag("missing") is None

    def _setup_ctx(self, monkeypatch, tmp_path):
        zh = tmp_path / "zh"
        zh.mkdir()
        f = zh / "api.md"
        f.write_text("# api\n", encoding="utf-8")
        monkeypatch.setattr(rb, "ZH_DIR", zh)
        monkeypatch.setattr(rb, "REPO_ROOT", tmp_path)
        return f

    def test_rollback_file_unsafe_path(self, tmp_path):
        assert rb.rollback_file(Path("/etc/passwd"), "v1") is False

    def test_rollback_file_success(self, monkeypatch, tmp_path):
        f = self._setup_ctx(monkeypatch, tmp_path)
        def fake_run(a, **k):
            assert a[0] == "git"
            if a[1] == "rev-parse":
                return subprocess.CompletedProcess(a, 0, stdout="deadbeef\n", stderr="")
            if a[1] == "show":
                return subprocess.CompletedProcess(a, 0, stdout="# old content\n", stderr="")
            raise AssertionError(f"unexpected git cmd {a}")
        monkeypatch.setattr(rb.subprocess, "run", fake_run)
        assert rb.rollback_file(f, "v1") is True
        assert f.read_text(encoding="utf-8") == "# old content\n"

    def test_rollback_file_tag_missing(self, monkeypatch, tmp_path):
        f = self._setup_ctx(monkeypatch, tmp_path)
        monkeypatch.setattr(rb.subprocess, "run",
                            lambda a, **k: subprocess.CompletedProcess(a, 1, stdout="", stderr="no tag"))
        assert rb.rollback_file(f, "v9") is False

    def test_rollback_file_git_show_fail(self, monkeypatch, tmp_path):
        f = self._setup_ctx(monkeypatch, tmp_path)
        def fake_run(a, **k):
            if a[1] == "rev-parse":
                return subprocess.CompletedProcess(a, 0, stdout="deadbeef\n", stderr="")
            # 模拟真实 run 的 check 语义：check=True 且非零返回码时抛错
            if k.get("check") and a[1] == "show":
                raise subprocess.CalledProcessError(1, a)
            return subprocess.CompletedProcess(a, 1, stdout="", stderr="err")
        monkeypatch.setattr(rb.subprocess, "run", fake_run)
        assert rb.rollback_file(f, "v1") is False

    def test_list_versions_sorted_desc(self, monkeypatch, tmp_path):
        f = self._setup_ctx(monkeypatch, tmp_path)
        def fake_run(a, **k):
            prefix = "translation/api.md/"
            return subprocess.CompletedProcess(
                a, 0,
                stdout=f"{prefix}v2\n{prefix}v10\n{prefix}v1\n", stderr="")
        monkeypatch.setattr(rb.subprocess, "run", fake_run)
        # 脚本按字符串降序排序（'v2' > 'v10' 为字符串序），行为即现状
        assert rb.list_versions(f) == ["v2", "v10", "v1"]

    def test_list_versions_unsafe_path(self, tmp_path):
        assert rb.list_versions(Path("/etc/passwd")) == []


# ---------- validate_code_examples ----------

class TestValidateCodeExamples:
    def test_extract_cpp_blocks_basic(self):
        content = "text\n\n```cpp\nint a;\n```\n\n```c++\nint b;\nint c;\n```\n"
        blocks = vc.extract_cpp_blocks(content)
        assert len(blocks) == 2
        assert blocks[0][1] == "int a;"
        assert blocks[1][1] == "int b;\nint c;"

    def test_extract_nested_warns(self):
        content = "```cpp\n```\n```\n"  # 空块（无内容不收录）
        assert vc.extract_cpp_blocks(content) == []

    def test_wrap_keeps_main(self):
        code = "#include <fmt/format.h>\nint main() { return 0; }\n"
        assert vc.wrap_code_for_compilation(code) == code

    def test_wrap_adds_includes_and_main(self):
        code = "fmt::print(\"{}\", 42);"
        w = vc.wrap_code_for_compilation(code)
        assert "#include <fmt/format.h>" in w
        assert "#include <fmt/ranges.h>" in w
        assert "int main()" in w and "return 0;" in w

    def test_validate_file_all_pass_with_mock_compile(self, monkeypatch, tmp_path):
        md = tmp_path / "sample.md"
        md.write_text("```cpp\nint x = 1;\n```\n", encoding="utf-8")
        monkeypatch.setattr(vc.subprocess, "run",
                            lambda a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""))
        assert vc.validate_file(md) == []

    def test_validate_file_reports_failures(self, monkeypatch, tmp_path):
        md = tmp_path / "sample.md"
        md.write_text("```cpp\nint x = 1;\n```\n\n```cpp\nint y = 2;\n```\n", encoding="utf-8")
        def fail(a, **k):
            return subprocess.CompletedProcess(a, 1, stdout="", stderr="compile error")
        monkeypatch.setattr(vc.subprocess, "run", fail)
        errors = vc.validate_file(md)
        assert len(errors) == 2
        assert "sample.md" in errors[0]

    def test_validate_file_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            vc.validate_file(tmp_path / "nope.md")


# ---------- generate_bilingual（端到端，tmp 隔离） ----------

import generate_bilingual as gb  # noqa: E402


def _mk_bilingual_env(tmp_path, monkeypatch, src_c, zh_c, excluded=False):
    """构造隔离的双语生成环境：source/zh/state 全部指向 tmp。"""
    src = tmp_path / "source"
    zh = tmp_path / "zh"
    src.mkdir()
    zh.mkdir()
    (src / "api.md").write_text(src_c, encoding="utf-8")
    (zh / "api.md").write_text(zh_c, encoding="utf-8")
    state = {
        "upstream_repo": "", "upstream_commit": "a" * 40, "upstream_version": "latest",
        "files": {"api.md": {"file_path": "api.md", "upstream_hash": "x",
                             "upstream_commit": "a" * 40, "excluded": excluded,
                             "segments": []}},
    }
    (tmp_path / ".translation-state.json").write_text(
        json.dumps(state, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(gb, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gb, "SOURCE_DIR", src)
    monkeypatch.setattr(gb, "ZH_DIR", zh)
    monkeypatch.setattr(gb, "OUT_DIR", zh / "bilingual")
    return src, zh


class TestGenerateBilingual:
    def test_generate_pages_and_about(self, tmp_path, monkeypatch):
        src_c = "# Core API\n\nCore paragraph about formatting.\n\n```cpp\nint a;\n```\n"
        zh_c = "# 核心 API\n\n关于格式化的核心段落。\n\n```cpp\nint a;\n```\n"
        _mk_bilingual_env(tmp_path, monkeypatch, src_c, zh_c)
        gb.main()
        page = (tmp_path / "zh" / "bilingual" / "api.md").read_text(encoding="utf-8")
        assert "双语对照：API 参考" in page
        assert "关于格式化的核心段落。" in page
        assert "Core paragraph about formatting." in page
        assert (tmp_path / "zh" / "bilingual" / "about.md").exists()
        # 代码块不做对照（原样保留）
        assert "```text\n```cpp" not in page

    def test_generate_skips_front_matter(self, tmp_path, monkeypatch):
        src_c = "---\nhide:\n  - toc\n---\n\n# T\n\nbody text here\n"
        zh_c = "---\nhide:\n  - toc\n---\n\n# 标题\n\n正文内容\n"
        _mk_bilingual_env(tmp_path, monkeypatch, src_c, zh_c)
        gb.main()
        page = (tmp_path / "zh" / "bilingual" / "api.md").read_text(encoding="utf-8")
        assert "hide:" not in page

    def test_generate_alignment_fail_on_count_mismatch(self, tmp_path, monkeypatch):
        _mk_bilingual_env(
            tmp_path, monkeypatch, "# T\n\npara one\n\npara two\n", "# 标题\n\n只有一段\n")
        with pytest.raises(SystemExit, match="ALIGNMENT FAIL"):
            gb.main()

    def test_generate_skips_excluded(self, tmp_path, monkeypatch):
        _mk_bilingual_env(
            tmp_path, monkeypatch, "# T\n\npara\n", "# 标题\n\n段落\n", excluded=True)
        gb.main()
        assert not (tmp_path / "zh" / "bilingual" / "api.md").exists()


# ---------- translate_batch（stub 行为 + known_fields 回归 + main dry-run） ----------

import translate_batch as tb  # noqa: E402


def _mk_tb_state(tmp_path, monkeypatch, segments):
    src = tmp_path / "source"
    src.mkdir()
    (src / "a.md").write_text("# A\n", encoding="utf-8")
    state = {"files": {"a.md": {"segments": segments}}}
    (tmp_path / ".ts.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(tb, "SOURCE_DIR", src)
    monkeypatch.setattr(tb, "STATE_FILE", tmp_path / ".ts.json")
    return tmp_path / ".ts.json"


class TestTranslateBatch:
    def test_build_prompt_contains_glossary_and_rules(self):
        seg = tb.Segment("id", "paragraph", "fmt::format", "h", "f.md", 1, 1, {})
        prompt = tb.build_prompt(seg, {"format string": "格式字符串"})
        assert "格式字符串" in prompt and "Glossary" in prompt
        assert "fmt::format" in prompt

    def test_translate_segment_stub_marks_zh_prefix(self):
        seg = tb.Segment("id", "paragraph", "hello", "h", "f.md", 1, 1, {})
        assert tb.translate_segment(seg, {}) == "[ZH] hello"

    def test_get_pending_filters_status_and_code(self, tmp_path, monkeypatch):
        # known_fields 过滤回归：额外键（status/error）不得使 Segment 构造崩溃
        segs = [
            {"id": "1", "type": "paragraph", "content": "x", "hash": "h",
             "file_path": "a.md", "line_start": 1, "line_end": 1, "metadata": {},
             "status": "pending", "error": "extra-key-safe"},
            {"id": "2", "type": "code_block", "content": "```", "hash": "h",
             "file_path": "a.md", "line_start": 2, "line_end": 2, "metadata": {},
             "status": "pending"},
            {"id": "3", "type": "paragraph", "content": "y", "hash": "h",
             "file_path": "a.md", "line_start": 3, "line_end": 3, "metadata": {},
             "status": "translated"},
        ]
        _mk_tb_state(tmp_path, monkeypatch, segs)
        pending = tb.get_pending_translations(tb.load_state())
        assert len(pending) == 1
        assert pending[0].segment.id == "1"

    def test_main_dry_run_lists_pending(self, tmp_path, monkeypatch, capsys):
        segs = [{"id": "1", "type": "paragraph", "content": "x", "hash": "h",
                 "file_path": "a.md", "line_start": 1, "line_end": 1,
                 "metadata": {}, "status": "pending"}]
        _mk_tb_state(tmp_path, monkeypatch, segs)
        monkeypatch.setattr(sys, "argv", ["translate_batch.py", "--all", "--dry-run"])
        tb.main()
        assert "Would translate" in capsys.readouterr().out

    def test_main_no_pending_is_noop(self, tmp_path, monkeypatch):
        segs = [{"id": "1", "type": "paragraph", "content": "x", "hash": "h",
                 "file_path": "a.md", "line_start": 1, "line_end": 1,
                 "metadata": {}, "status": "translated"}]
        _mk_tb_state(tmp_path, monkeypatch, segs)
        monkeypatch.setattr(sys, "argv", ["translate_batch.py", "--all"])
        tb.main()  # 无 pending：直接返回，不写 zh/、不动 state
        assert not (tmp_path / "zh").exists()

    def test_glossary_loader_reads_yaml(self, tmp_path, monkeypatch):
        g = tmp_path / "glossary.yml"
        g.write_text("terms:\n  - en: \"width\"\n    zh: \"宽度\"\n", encoding="utf-8")
        monkeypatch.setattr(tb, "GLOSSARY_FILE", g)
        assert tb.load_glossary() == {"width": "宽度"}
        # 坏 YAML 优雅降级
        g.write_text("terms: [unclosed", encoding="utf-8")
        assert tb.load_glossary() == {}


# ---------- validate_translation（负向分支 + 辅助函数） ----------

import validate_translation as vt  # noqa: E402


class TestValidateTranslationBranches:
    def _pair(self, tmp_path, src_c, zh_c):
        s = tmp_path / "s.md"
        t = tmp_path / "t.md"
        s.write_text(src_c, encoding="utf-8")
        t.write_text(zh_c, encoding="utf-8")
        return s, t

    def test_missing_target_is_error(self, tmp_path):
        s = tmp_path / "s.md"
        s.write_text("# A\n", encoding="utf-8")
        r = vt.validate_file(s, tmp_path / "missing.md", {})
        assert any("Target file not found" in e for e in r["errors"])

    def test_missing_source_is_error(self, tmp_path):
        r = vt.validate_file(tmp_path / "nope.md", tmp_path / "t.md", {})
        assert any("Source file not found" in e for e in r["errors"])

    def test_code_block_modified_is_error(self, tmp_path):
        s, t = self._pair(tmp_path, "```cpp\nint a;\n```\n", "```cpp\nint b;\n```\n")
        r = vt.validate_file(s, t, {})
        assert any("Code block" in e for e in r["errors"])

    def test_protected_placeholder_is_error(self, tmp_path):
        s, t = self._pair(tmp_path, "text here\n", "译文 {{PROTECTED_CODE_XYZ}} 残留\n")
        r = vt.validate_file(s, t, {})
        assert any("PROTECTED_" in e for e in r["errors"])

    def test_url_count_mismatch_is_warning(self, tmp_path):
        s, t = self._pair(tmp_path, "see [a](https://x.com) here\n", "见链接这里\n")
        r = vt.validate_file(s, t, {})
        assert any("URL count mismatch" in w for w in r["warnings"])

    def test_heading_count_mismatch_is_warning(self, tmp_path):
        s, t = self._pair(tmp_path, "# One\n\n# Two\n", "# 只有\n")
        r = vt.validate_file(s, t, {})
        assert any("Heading count mismatch" in w for w in r["warnings"])

    def test_glossary_violation_is_warning(self, tmp_path):
        s, t = self._pair(tmp_path, "the format string here\n", "这里的格式串\n")
        r = vt.validate_file(s, t, {"format string": "格式字符串"})
        assert any("format string" in w for w in r["warnings"])

    def test_normalize_tag_specials(self):
        assert vt.normalize_tag("<https://x.com>") is None
        assert vt.normalize_tag("<!-- c -->") is None
        assert vt.normalize_tag("<b>") == ("b", False)
        assert vt.normalize_tag("</b>") == ("b", True)
        assert vt.normalize_tag("not a tag") is None

    def test_tags_balanced(self):
        assert vt.check_pairing(["<p>", "<b>", "</b>", "</p>"]) is True
        assert vt.check_pairing(["<p>", "<b>", "</p>"]) is False
        assert vt.check_pairing(["<img src='x'>"]) is True
        assert vt.check_pairing([]) is True
        # tag_type_counts 以 (标签名, 是否闭合) 为键计数
        assert vt.tag_type_counts(["<p>", "<p>", "</p>"]) == {("p", False): 2, ("p", True): 1}


# ---------- main() 流程（argparse 驱动，subprocess 全 mock） ----------

class TestMainFlows:
    def test_build_site_main_success(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(
            bs.subprocess, "run",
            lambda a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""))
        monkeypatch.setattr(sys, "argv", ["build_site.py"])
        bs.main()

    def test_build_site_main_failure_exits(self, monkeypatch, tmp_path):
        monkeypatch.setattr(bs, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(
            bs.subprocess, "run",
            lambda a, **k: subprocess.CompletedProcess(a, 1, stdout="", stderr="e"))
        monkeypatch.setattr(sys, "argv", ["build_site.py"])
        with pytest.raises(SystemExit) as e:
            bs.main()
        assert e.value.code == 1

    def test_rollback_main_file_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(rb, "ZH_DIR", tmp_path / "zh")
        monkeypatch.setattr(sys, "argv",
                            ["rollback.py", "--file", str(tmp_path / "gone.md")])
        with pytest.raises(SystemExit) as e:
            rb.main()
        assert e.value.code == 1

    def test_rollback_main_outside_zh_rejected(self, monkeypatch, tmp_path):
        outside = tmp_path / "evil.md"
        outside.write_text("x", encoding="utf-8")
        monkeypatch.setattr(rb, "ZH_DIR", tmp_path / "zh")
        monkeypatch.setattr(sys, "argv", ["rollback.py", "--file", str(outside)])
        with pytest.raises(SystemExit) as e:
            rb.main()
        assert e.value.code == 1

    def test_rollback_main_list_no_versions(self, monkeypatch, tmp_path, capsys):
        zh = tmp_path / "zh"
        zh.mkdir()
        f = zh / "api.md"
        f.write_text("# api\n", encoding="utf-8")
        monkeypatch.setattr(rb, "ZH_DIR", zh)
        monkeypatch.setattr(rb, "list_versions", lambda fp: [])
        monkeypatch.setattr(sys, "argv", ["rollback.py", "--file", str(f), "--list"])
        rb.main()
        assert "No versions found" in capsys.readouterr().out

    def test_rollback_main_requires_to_version(self, monkeypatch, tmp_path):
        zh = tmp_path / "zh"
        zh.mkdir()
        f = zh / "api.md"
        f.write_text("# api\n", encoding="utf-8")
        monkeypatch.setattr(rb, "ZH_DIR", zh)
        monkeypatch.setattr(sys, "argv", ["rollback.py", "--file", str(f)])
        with pytest.raises(SystemExit) as e:
            rb.main()
        assert e.value.code == 1

    def test_rollback_main_success_exits_zero(self, monkeypatch, tmp_path):
        zh = tmp_path / "zh"
        zh.mkdir()
        f = zh / "api.md"
        f.write_text("# api\n", encoding="utf-8")
        monkeypatch.setattr(rb, "ZH_DIR", zh)
        monkeypatch.setattr(rb, "rollback_file", lambda fp, v: True)
        monkeypatch.setattr(sys, "argv",
                            ["rollback.py", "--file", str(f), "--to-version", "v1"])
        with pytest.raises(SystemExit) as e:
            rb.main()
        assert e.value.code == 0

    def test_compile_gpp_success_and_timeout(self, monkeypatch):
        monkeypatch.setattr(
            vc.subprocess, "run",
            lambda a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""))
        ok = vc.compile_gpp("int main() {}")
        assert ok.success is True

        def raise_timeout(a, **k):
            raise subprocess.TimeoutExpired(a, 30)
        monkeypatch.setattr(vc.subprocess, "run", raise_timeout)
        assert vc.compile_gpp("int main() {}").success is False

    def test_validate_code_examples_main_with_file_arg(self, monkeypatch, tmp_path):
        zh = tmp_path / "zh"
        zh.mkdir()
        (zh / "s.md").write_text("no code blocks here\n", encoding="utf-8")
        monkeypatch.setattr(vc, "ZH_DIR", zh)
        monkeypatch.setattr(
            vc.subprocess, "run",
            lambda a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""))
        monkeypatch.setattr(sys, "argv", ["vce.py", str(zh / "s.md")])
        with pytest.raises(SystemExit) as e:
            vc.main()
        assert e.value.code == 0

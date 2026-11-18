"""translate_batch.py / validate_translation.py 状态流转与校验测试。"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import translate_batch as tb  # noqa: E402
import validate_translation as vt  # noqa: E402


@pytest.fixture
def sample_segment():
    return tb.Segment(
        id="api.md-p-0",
        type="paragraph",
        content="The {fmt} library provides fast formatting.",
        hash=tb.compute_hash("The {fmt} library provides fast formatting."),
        file_path="api.md",
        line_start=1,
        line_end=1,
        metadata={"section": ""},
    )


class TestTranslateBatch:
    def test_compute_hash(self, sample_segment):
        assert len(sample_segment.hash) == 16
        assert tb.compute_hash("x") != tb.compute_hash("y")

    def test_mock_translation_marks_status(self, sample_segment):
        glossary = {"formatting": "格式化"}
        out = tb.translate_segment(sample_segment, glossary)
        assert out.startswith("[ZH]"), "mock 翻译应带 [ZH] 标记以便识别"

    def test_build_prompt_contains_glossary_and_rules(self, sample_segment):
        glossary = {"format string": "格式字符串"}
        prompt = tb.build_prompt(sample_segment, glossary)
        assert "格式字符串" in prompt
        assert sample_segment.content in prompt
        assert "MUST follow" in prompt or "Rules" in prompt

    def test_pending_excludes_code_blocks(self, tmp_path, monkeypatch):
        """code_block 类型段落不进入待翻译列表（代码保护核心保证）。"""
        state = {
            "files": {
                "api.md": {
                    "file_path": "api.md",
                    "upstream_hash": "x",
                    "upstream_commit": "c",
                    "segments": [
                        {"id": "api.md-code-0", "type": "code_block", "content": "```cpp\nx\n```",
                         "hash": "h", "file_path": "api.md", "line_start": 1, "line_end": 3,
                         "metadata": {}, "status": "pending"},
                        {"id": "api.md-p-0", "type": "paragraph", "content": "text",
                         "hash": "h2", "file_path": "api.md", "line_start": 5, "line_end": 5,
                         "metadata": {}, "status": "pending"},
                        {"id": "api.md-p-1", "type": "paragraph", "content": "done",
                         "hash": "h3", "file_path": "api.md", "line_start": 7, "line_end": 7,
                         "metadata": {}, "status": "translated"},
                    ],
                }
            }
        }
        monkeypatch.setattr(tb, "SOURCE_DIR", tmp_path / "source")
        monkeypatch.setattr(tb, "ZH_DIR", tmp_path / "zh")
        (tmp_path / "source").mkdir()
        (tmp_path / "source" / "api.md").write_text("x", encoding="utf-8")
        pending = tb.get_pending_translations(state)
        ids = [p.segment.id for p in pending]
        assert ids == ["api.md-p-0"], "code_block 与已翻译段不应出现在待翻译列表"

    def test_write_translated_file(self, tmp_path, monkeypatch, sample_segment):
        zh_dir = tmp_path / "zh"
        monkeypatch.setattr(tb, "ZH_DIR", zh_dir)
        target = zh_dir / "api.md"
        tb.write_translated_file(target, [sample_segment])
        assert target.exists()
        assert sample_segment.content in target.read_text(encoding="utf-8")


class TestValidateTranslation:
    def test_extract_code_blocks(self):
        content = "a\n```cpp\nint x;\n```\nb\n```\nplain\n```\nc"
        blocks = vt.extract_code_blocks(content)
        assert len(blocks) == 2
        assert "int x;" in blocks[0]

    def test_extract_inline_code(self):
        content = "use `fmt::format` and `FMT_STRING` here"
        blocks = vt.extract_inline_code(content)
        assert len(blocks) == 2

    def test_extract_urls(self):
        content = "[docs](https://fmt.dev) and [gh](https://github.com/fmtlib/fmt)"
        urls = vt.extract_urls(content)
        assert urls == ["https://fmt.dev", "https://github.com/fmtlib/fmt"]

    def test_validate_file_detects_modified_code_block(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text("```cpp\nint x = 1;\n```", encoding="utf-8")
        tgt.write_text("```cpp\nint x = 2;\n```", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("Code block 0 modified" in e for e in result["errors"])

    def test_validate_file_detects_placeholder_residue(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text("```cpp\nx\n```", encoding="utf-8")
        tgt.write_text("```cpp\nx\n```\n残留 {{PROTECTED_CODE_BLOCK_deadbeef}}", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("PROTECTED_" in e for e in result["errors"])

    def test_validate_file_glossary_warning(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text("A format string example.", encoding="utf-8")
        tgt.write_text("一个 format string 示例。", encoding="utf-8")
        result = vt.validate_file(src, tgt, {"format string": "格式字符串"})
        assert any("not translated" in w for w in result["warnings"])

    def test_validate_file_missing_files(self, tmp_path):
        result = vt.validate_file(tmp_path / "no.md", tmp_path / "no2.md", {})
        assert result["errors"]


class TestValidateHTMLTwoLevel:
    """HTML 两级检查（按类型计数 + 配对完整性）——用户认可的放宽策略。"""

    def test_reordered_tags_pass_without_warnings(self, tmp_path):
        """语序调整导致 <b>/<code> 句内互换：必须 0 错误 0 警告。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<b>fast</b> than <code>sprintf</code> here', encoding="utf-8")
        tgt.write_text('比 <code>sprintf</code> 更<b>快</b>的地方', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_tag_type_count_mismatch_is_error(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<div><b>bold</b></div>', encoding="utf-8")
        tgt.write_text('<b>bold</b>', encoding="utf-8")  # 丢了 <div>
        result = vt.validate_file(src, tgt, {})
        assert any("HTML tag type counts mismatch" in e for e in result["errors"])

    def test_unbalanced_pairing_is_error(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<div><b>text</b></div>', encoding="utf-8")
        tgt.write_text('<div><b>text</div>', encoding="utf-8")  # 交叉/缺配对
        result = vt.validate_file(src, tgt, {})
        assert any("unbalanced" in e for e in result["errors"])

    def test_void_tags_ignored_in_pairing(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<p>chart <img src="perf.svg"> done</p>', encoding="utf-8")
        tgt.write_text('<p>图表 <img src="perf.svg"> 完成</p>', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_comments_not_counted_as_tags(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<!-- note -->\ntext', encoding="utf-8")
        tgt.write_text('<!-- 注释 -->\n正文', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []


class TestValidatorRefinements:
    """2026-11-19 get-started.md 校验发现的三项校验器修正。"""

    def test_autolinks_not_treated_as_tags(self, tmp_path):
        """<https://...> 自动链接不得被视为未闭合的 <https> 标签。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('- <https://cppget.org/fmt/> released\n- <https://x.org> custom\n',
                       encoding="utf-8")
        tgt.write_text('- <https://cppget.org/fmt/>：正式版本\n- <https://x.org>：自定义\n',
                       encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_inline_code_multiset_pass_on_reorder(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('set `A` to `TRUE` for `B`', encoding="utf-8")
        tgt.write_text('为 `B` 将 `A` 设为 `TRUE`', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_inline_code_multiset_catches_missing_span(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('use `fmt::format` and `FMT_STRING`', encoding="utf-8")
        tgt.write_text('使用 `fmt::format`', encoding="utf-8")  # 丢了 FMT_STRING
        result = vt.validate_file(src, tgt, {})
        assert any("multiset mismatch" in e for e in result["errors"])

    def test_glossary_check_ignores_code_identifiers(self, tmp_path):
        """`src/format.cc` 之类代码标识符不得触发 'format'→'格式化' 术语误报。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('compile `src/format.cc` with your code', encoding="utf-8")
        tgt.write_text('将 `src/format.cc` 与您的代码一同编译', encoding="utf-8")
        result = vt.validate_file(src, tgt, {"format": "格式化"})
        assert not any("'format'" in w for w in result["warnings"])

    def test_anchor_tag_with_absolute_url_pairs_correctly(self, tmp_path):
        """回归：<a href="https://..."> 含 ：//，不得被自动链接规则误跳过
        （曾导致其 </a> 无可配对，index.md 源文件误报不平衡）。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('<p>see <a href="https://x.org/y">docs</a> and <a href="api#x">more</a></p>',
                       encoding="utf-8")
        tgt.write_text('<p>请参阅 <a href="https://x.org/y">文档</a>与 <a href="api#x">更多</a></p>',
                       encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_indented_code_placeholders_ignored(self, tmp_path):
        """缩进式代码块中的 <your-target> 不得被判为未闭合 HTML 标签。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        block = "    target_link_libraries(<your-target> fmt::fmt)\n\n    find_package(fmt)\n"
        src.write_text(block, encoding="utf-8")
        tgt.write_text(block, encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_pre_block_indented_lines_survive_strip(self, tmp_path):
        """回归：语法块内部 ≥4 空格缩进的续行（如语法文法）是真实内容，
        不得被缩进代码块启发式剔除——曾导致 </code> 消失、配对失败。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        block = ('<pre><code class="language-json"\n'
                 '>spec ::= "a" | "b"</code>\n'
                 '</pre>\n')
        src.write_text(block, encoding="utf-8")
        tgt.write_text(block, encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_pre_block_indented_continuation_kept(self, tmp_path):
        """跨行 <code ...> 开标签 + 缩进续行 + 尾部 </code> 的完整配对。"""
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        block = ('<pre><code class="language-json"\n'
                 '>type ::= "a" |\n'
                 '                "b"</code>\n'
                 '</pre>\n')
        src.write_text(block, encoding="utf-8")
        tgt.write_text(block, encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_glossary_check_still_matches_prose(self, tmp_path):
        src = tmp_path / "s.md"
        tgt = tmp_path / "t.md"
        src.write_text('A format string is checked at compile time.', encoding="utf-8")
        tgt.write_text('格式字符串会在编译时被检查。', encoding="utf-8")
        result = vt.validate_file(src, tgt, {"format string": "格式字符串"})
        assert result["warnings"] == []


class TestStateRoundtrip:
    def test_state_file_matches_real_segment_count(self):
        """真实状态文件与分段函数输出一致性（防状态漂移）。"""
        state_file = REPO_ROOT / ".translation-state.json"
        if not state_file.exists():
            pytest.skip(".translation-state.json not generated yet")
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["upstream_commit"] == "14ac0d5a9d40aef14f50954069c1e10971abb0b2"
        assert len(state["files"]) == 5
        total = sum(len(f["segments"]) for f in state["files"].values())
        assert total == 1117

    def test_all_segments_have_known_status(self):
        """状态字段只允许流水线已定义的值，防止脏数据混入。"""
        state_file = REPO_ROOT / ".translation-state.json"
        if not state_file.exists():
            pytest.skip(".translation-state.json not generated yet")
        known = {"pending", "translated", "failed", "reviewed"}
        state = json.loads(state_file.read_text(encoding="utf-8"))
        for fn, fs in state["files"].items():
            for seg in fs["segments"]:
                status = seg.get("status", "pending")
                assert status in known, f"{fn}/{seg['id']} unexpected status {status}"

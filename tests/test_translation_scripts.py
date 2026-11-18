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

    def test_all_segments_have_status_pending_or_absent(self):
        state_file = REPO_ROOT / ".translation-state.json"
        if not state_file.exists():
            pytest.skip(".translation-state.json not generated yet")
        state = json.loads(state_file.read_text(encoding="utf-8"))
        for fn, fs in state["files"].items():
            for seg in fs["segments"]:
                status = seg.get("status", "pending")
                assert status == "pending", f"{fn}/{seg['id']} unexpected status {status}"

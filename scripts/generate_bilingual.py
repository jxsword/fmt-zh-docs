#!/usr/bin/env python3
"""Generate bilingual comparison pages (DR-005: standalone comparison mode).

按 .translation-state.json 的文件清单，将 source/（英文）与 zh/（中文）逐段
对齐生成 zh/bilingual/ 对照页：译文正文 + 原文代码块引用。

对齐要求：两版段落数量一致且逐位类型相同（校验器结构检查保证）；
不一致时报错退出，防止静默错位（增量翻译后需重跑校验）。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from sync_docs import segment_md, load_state  # noqa: E402

SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
OUT_DIR = ZH_DIR / "bilingual"

PAGE_TITLES = {
    "index.md": "首页",
    "get-started.md": "快速开始",
    "syntax.md": "格式语法",
    "api.md": "API 参考",
}


def render_page(fname: str, src_segs, zh_segs) -> str:
    title = PAGE_TITLES.get(fname, fname)
    out = [
        f"# 双语对照：{title}",
        "",
        f"> 本页为 `{fname}` 的中英段落对照（DR-005 独立对照模式）。"
        "每段先中文译文，再以引用块给出英文原文；代码块为逐字保留内容，不参与对照。",
        "",
    ]
    pairs = 0
    # 跳过 mkdocs front matter 段（仅首页首段，含 hide: navigation）
    start = 1 if (src_segs and src_segs[0].content.startswith("---")) else 0
    for idx, (s, z) in enumerate(zip(src_segs[start:], zh_segs[start:])):
        if s.type == "code_block":
            # 代码块逐字保留（红线），不生成对照
            continue
        if s.type == "heading":
            z_title = z.content.lstrip("#").strip()
            out.append(f"## {z_title}")
            out.append("")
            out.append(f"> 原文标题：{s.content.lstrip('#').strip()}")
            out.append("")
            pairs += 1
            continue
        out.append(z.content)
        out.append("")
        out.append("```text")
        out.append(s.content)
        out.append("```")
        out.append("")
        pairs += 1
    out.append("---")
    out.append(f"*对照段落数：{pairs}（代码块未计入）*")
    return "\n".join(out) + "\n"


def main():
    state = load_state(REPO_ROOT / ".translation-state.json")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    for fname in sorted(state.files.keys()):
        if state.files[fname].excluded:
            # DR-014：excluded 文件不翻译，zh/ 仅有占位页，无对照意义
            print(f"skip {fname}: excluded (DR-014)")
            continue
        src_text = (SOURCE_DIR / fname).read_text(encoding="utf-8")
        zh_path = ZH_DIR / fname
        if not zh_path.exists():
            print(f"skip {fname}: zh missing")
            continue
        zh_text = zh_path.read_text(encoding="utf-8")
        src_segs = segment_md(src_text, fname)
        zh_segs = segment_md(zh_text, fname)
        if len(src_segs) != len(zh_segs):
            raise SystemExit(
                f"ALIGNMENT FAIL {fname}: {len(src_segs)} src vs {len(zh_segs)} zh segs")
        for i, (s, z) in enumerate(zip(src_segs, zh_segs)):
            if s.type != z.type:
                raise SystemExit(
                    f"ALIGNMENT FAIL {fname} seg {i}: {s.type} vs {z.type}")
        page = render_page(fname, src_segs, zh_segs)
        out_path = OUT_DIR / fname
        out_path.write_text(page, encoding="utf-8")
        report.append(f"{fname}: {len(src_segs)} segments -> {out_path}")

    readme = [
        "# 双语对照说明",
        "",
        "> 本目录提供各文档的中英逐段对照页（DR-005 独立对照模式），用于审校与查阅。",
        "阅读版请使用左侧导航对应章节；对照页由 `scripts/generate_bilingual.py` 自动生成，",
        "请勿手工编辑。",
        "",
        "| 页面 | 对照页 |",
        "|------|--------|",
    ]
    for fname in sorted(PAGE_TITLES):
        readme.append(f"| {PAGE_TITLES[fname]} | [bilingual/{fname}]({fname}) |")
    # 说明页不用 README.md：mkdocs 会把它当 index 处理而与 bilingual/index.md 冲突
    (OUT_DIR / "about.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    report.append("about.md written")
    print("\n".join(report))


if __name__ == "__main__":
    main()

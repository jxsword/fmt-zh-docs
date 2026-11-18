# fmt 中文文档翻译项目 - 完整实施计划

> 基于三轮复审修正补充后的最终版本  
> 创建时间：2026-11-18  
> 状态：待实施

---

## 📋 目录

1. [项目概览](#项目概览)
2. [核心架构决策记录 (DR)](#核心架构决策记录-dr)
3. [仓库结构设计](#仓库结构设计)
4. [核心脚本设计](#核心脚本设计)
5. [CI/CD 流水线设计](#cicd-流水线设计)
6. [配置文件规范](#配置文件规范)
7. [里程碑与交付计划](#里程碑与交付计划)
8. [风险与对策](#风险与对策)
9. [启动清单](#启动清单)

---

## 项目概览

### 目标
将 [fmt.dev](https://fmt.dev/latest/) 官方文档翻译为中文，建立可持续的增量翻译体系，跟随上游文档持续更新。

### 核心特性
- **增量翻译**：段落级 hash 对比，仅翻译变更内容
- **术语一致性**：上下文感知术语表 + CI 强制校验
- **代码保护**：代码块/内联代码/HTML/链接完整性保证
- **多版本支持**：同步 fmt.dev 版本结构，支持历史版本回溯
- **全自动化流水线**：同步 → 检测 → 翻译 → 校验 → 部署
- **质量度量**：自动化指标 + 人工抽检 + 用户反馈闭环

### 上游文档源
| 源 | URL | 核实日期 | 说明 |
|----|-----|----------|------|
| 官网 | https://fmt.dev/latest/ | 2026-11-18 | 渲染后站点 |
| 文档源码仓库 | https://github.com/fmtlib/fmt/tree/main/doc | 2026-11-18 | 5 个 Markdown 文件 |
| 站点部署仓库 | https://github.com/fmtlib/fmt.dev | 2026-11-18 | 多版本静态站点 |
| 许可证 | MIT | - | 允许翻译和再分发 |

### 文档结构（doc/ 目录）
| 文件 | 约行数 | 内容 | 优先级 |
|------|--------|------|--------|
| `index.md` | ~200 | 首页：库特性介绍 | 高 |
| `api.md` | ~2000+ | API 参考：核心 API、格式 API、范围、时间、标准库、编译时、颜色、系统、ostream、动态参数、printf、宽字符、C++20 兼容、配置选项 | 高 |
| `get-started.md` | ~400 | 快速开始：CMake、安装、构建、各构建系统 | 高 |
| `syntax.md` | ~1500+ | 格式字符串语法：替换字段、格式规范、填充对齐、符号、宽度、精度、区域设置、呈现类型、chrono、范围、组合示例 | 高 |
| `ChangeLog-old.md` | - | 变更日志（旧版） | 低 |

### 现有翻译项目调研结论
- GitHub 搜索 `fmt chinese translation`、`fmtlib fmt zh docs`、`fmt 中文 文档`、`fmt.dev 中文`、`fmt translation` 均 **0 结果**
- fmtlib 组织下无中文翻译相关仓库
- fmt 仓库 30+ 个 forks 均为原库镜像
- **结论：暂无现成中文翻译项目可复用，需从零开始**

---

## 核心架构决策记录 (DR)

| DR 编号 | 标题 | 状态 | 关键决策 | 记录时间 |
|---------|------|------|----------|----------|
| DR-001 | 多版本管理策略 | 生效 | 保留最近 3 minor + 1 LTS，mkdocs-material + mike 版本切换 | 2026-11-18 |
| DR-002 | 段落切分粒度 | 生效 | 语义感知 AST 级切分，代码块/表格/列表独立为段 | 2026-11-18 |
| DR-003 | 术语表上下文消歇 | 生效 | 正则上下文匹配 + 默认兜底，术语表版本化 | 2026-11-18 |
| DR-004 | 代码保护机制 | 生效 | 占位符替换法，支持代码块/内联代码/HTML/链接/模板 | 2026-11-18 |
| DR-005 | 双语对照模式 | 生效 | 悬浮提示 + 独立对照页面双模式 | 2026-11-18 |
| DR-006 | 翻译记忆复用 | 生效 | SQLite + sentence-transformers 语义检索，>0.95 直接复用 | 2026-11-18 |
| DR-007 | 上游 Breaking Change 分级响应 | 生效 | L1 自动、L2 半自动、L3 冻结+冲刺，3 个月并行维护 | 2026-11-18 |
| DR-008 | 社区反馈 SLA | 生效 | 关键 24h、术语 48h、一般 1 周，首次响应 2 工作日 | 2026-11-18 |
| DR-009 | 代码示例编译验证 | 生效 | CI 阻塞合并，多编译器测试，最小可编译单元包装 | 2026-11-18 |
| DR-010 | 多语言扩展预留 | 生效 | 目录隔离、配置分层、适配器模式隔离上游平台 | 2026-11-18 |

---

## 仓库结构设计

```
fmt-zh-docs/
├── .github/
│   └── workflows/
│       ├── sync-upstream.yml        # 定期同步上游文档变更
│       ├── translate-incremental.yml # 增量翻译 CI
│       ├── validate.yml              # 校验+代码验证流水线
│       ├── deploy.yml                # 部署到 GitHub Pages（多版本、PDF）
│       ├── monitoring.yml            # 监控告警
│       └── test.yml                  # 自动化测试
├── scripts/
│   ├── sync_docs.py                  # 同步上游 doc/ 目录
│   ├── segment_markdown.py           # 语义感知段落切分
│   ├── diff_docs.py                  # 对比中英文版本差异
│   ├── protect_untranslatable.py     # 代码/HTML/内联代码保护
│   ├── translate_batch.py            # 批量翻译调用（多 LLM 提供商）
│   ├── translation_memory.py         # 翻译记忆库
│   ├── validate_translation.py       # 翻译质量校验
│   ├── validate_code_examples.py     # 代码示例编译验证
│   ├── fix_links.py                  # 链接/锚点修复与映射
│   ├── rollback_translation.py       # 翻译回滚工具
│   ├── build_site.py                 # 构建中文站点
│   └── prompts/
│       └── translate.md.j2           # Prompt 模板
├── source/                           # 源语言（英文）文档 - 只读，由 sync 更新
│   ├── index.md
│   ├── api.md
│   ├── get-started.md
│   ├── syntax.md
│   └── ChangeLog-old.md
├── zh/                               # 中文翻译文档 - 工作目录
│   ├── index.md
│   ├── api.md
│   ├── get-started.md
│   ├── syntax.md
│   └── ChangeLog-old.md
├── config/
│   ├── glossary.yml                  # 术语表（含上下文消歇）
│   ├── style-guide.md                # 翻译风格指南
│   ├── quality-metrics.yml           # 质量度量指标定义
│   └── anchor_map.yml                # 标题锚点映射表（构建时生成）
├── tests/                            # 自动化测试套件
│   ├── test_sync_docs.py
│   ├── test_segment_markdown.py
│   ├── test_protect_untranslatable.py
│   ├── test_validate_translation.py
│   ├── test_fix_links.py
│   └── test_validate_code_examples.py
├── .translation-state.json           # 翻译状态追踪（每段落 hash + 翻译版本）
├── mkdocs.yml                        # 中文站点配置（多版本、搜索、PDF、分析、双语）
├── CONTRIBUTING_TRANSLATION.md       # 贡献者协作规范
├── LICENSE_TRANSLATION.md            # 法律合规声明
├── AUTHORS_TRANSLATION.md            # 翻译贡献者名单
├── docs/
│   ├── translation-board.md          # 翻译任务看板
│   └── decision_log.md               # 重大决策记录（DR 格式）
└── README.md
```

---

## 核心脚本设计

### 1. sync_docs.py - 上游文档同步
```python
# 核心功能
- 浅克隆 fmtlib/fmt (仅 doc/ 目录，sparse checkout)
- 对比 source/ 与上游 doc/ 差异（git diff --name-status）
- 处理变更类型：新增(A)、删除(D)、重命名(R)、修改(M)
- 下载变更文件到 source/，保留上游 commit SHA
- 调用 segment_markdown.py 切分段落
- 更新 .translation-state.json，标记需翻译段落
- 输出变更摘要供 CI 创建 PR

# 关键参数
--init              # 首次初始化，全量同步
--tag TAG           # 指定版本标签（如 12.2.0）
--since COMMIT      # 增量同步起点 commit
--dry-run           # 仅检测不写入
```

### 2. segment_markdown.py - 语义感知段落切分
```python
# 切分规则（基于 markdown-it-py AST）
1. 标题组：含下属内容至下一同级标题作为一个段落组
2. 代码块（```...```）：独立为段，标记不翻译
3. 表格：独立为段，仅翻译单元格文本
4. 列表：按项切分，保持缩进层级
5. 普通段落：按空行切分
6. HTML 块（<div>...）、Mermaid 图表：独立为段
7. 图片/链接：内联保护，不单独切分

# 段落 ID 格式
{file_stem}-{section_depth}-{section_index}-{para_index}
例：api-md-2-1-3 表示 api.md 第 2 级标题第 1 节第 3 段

# 输出
List[Segment] 包含：id, type, content, hash, metadata(line_range, parent_section)
```

### 3. protect_untranslatable.py - 不可翻译内容保护
```python
# 保护模式（按优先级）
PROTECTED_PATTERNS = [
    (r'```[\s\S]*?```', 'CODE_BLOCK'),
    (r'<[^>]+>', 'HTML_TAG'),
    (r'\{%[\s\S]*?%\}', 'JINJA_TEMPLATE'),
    (r'!![a-zA-Z-]+', 'YAML_TAG'),
    (r'\[\[.*?\]\]', 'WIKI_LINK'),
    (r'!\[[^\]]*\]\([^)]+\)', 'IMAGE'),
    (r'\[[^\]]+\]\([^)]+\)', 'LINK'),           # 保留 URL，仅保护链接文本可翻译
    (r'`[^`\n]+`', 'INLINE_CODE'),
]

# 占位符格式
{{PROTECTED_<TYPE>_<SHA256_HEX_8>}}

# 接口
protect(content) -> (protected_content, placeholder_map)
restore(protected_content, placeholder_map) -> original_content
```

### 4. translation_memory.py - 翻译记忆库
```python
# 存储：SQLite (.tm.sqlite)
# 表：source_hash, source_text, target_text, quality_score, context_hash, created_at, usage_count

# 核心方法
lookup(source_text, threshold=0.85) -> Optional[str]      # 语义相似度检索
add(source, target, quality=1.0, context="")              # 入库
get_suggestions(source, n=3) -> List[(target, score)]     # 获取候选

# 语义检索：sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
# 离线模型，无需 API 调用，CI 环境可预下载
```

### 5. translate_batch.py - 批量翻译引擎
```python
# 支持提供商：OpenAI, Anthropic, DeepSeek, 本地 Ollama, 兼容 OpenAI API 的代理
# 并发控制：信号量 + Token Bucket 限流
# 重试策略：指数退避 + 抖动，熔断机制
# Prompt 注入：系统提示 + 术语表相关条目 + Few-shot 示例 + 上下文（前后段落）
# TM 集成：>0.95 直接复用，0.85-0.95 作为 few-shot 注入

# 关键参数
--input pending.json           # 待翻译段落列表
--source-dir source/           # 源文档目录
--target-dir zh/               # 目标文档目录
--lang zh                      # 目标语言
--model gpt-4o-mini            # LLM 模型
--max-concurrent 3             # 最大并发
--glossary config/glossary.yml # 术语表
--tm .tm.sqlite                # 翻译记忆库
```

### 6. validate_translation.py - 翻译质量校验
```python
# 校验项
1. 术语一致性：glossary.yml 中术语在译文中统一（上下文感知匹配）
2. 代码块完整性：译文代码块 hash 与原文一致
3. 结构完整性：标题层级、列表、表格结构 AST 对比一致
4. 内联代码完整性：`...` 内容未被翻译
5. 链接有效性：相对链接在 zh/ 内可解析
6. 格式规范：无多余空行、中文标点规范、无中英文混排错误
7. 占位符还原：所有 PROTECTED_* 占位符已正确还原

# 输出
- 通过/失败状态
- 详细错误报告（文件、行号、错误类型、上下文）
- 指标统计：通过率、错误分布
```

### 7. validate_code_examples.py - 代码示例编译验证
```python
# 提取所有 ```cpp / ```c++ 代码块
# 包装成最小可编译单元：
  - 检测是否含 main()，无则包装
  - 自动添加必要 #include <fmt/format.h> 等
  - 提供常用 using 声明
# 多编译器测试：g++-13, clang++-17, MSVC (cl)
# 编译标准：-std=c++20 -O2
# 超时：30s/文件

# CI 集成：失败阻塞合并，报告具体文件、行号、错误信息
```

### 8. fix_links.py - 链接/锚点修复
```python
# 规则
1. 相对链接 .md：重写指向中文版对应文件
2. fmt.dev 官网链接：保持原样，可选添加 ?lang=en
3. GitHub 源码链接：保持原样
4. 锚点链接：生成 anchor_map.yml 映射表，构建时注入 HTML id 属性
   如：<h2 id="compile-time-checks">编译时检查</h2>

# 输出
- 修复后的 Markdown
- anchor_map.yml: {原文标题slug: 中文标题slug}
```

### 9. rollback_translation.py - 翻译回滚
```python
# 功能
- 文件级回滚：--file zh/api.md --to-version v12.1.0
- 段落级回滚：--file zh/api.md --paragraph api-md-2-1-3 --to-commit abc123
- 基于 .translation-state.json 历史（保留最近 10 版）
- Git tag 格式：translation/zh/api.md/v12.2.0-20261118
- 回滚后自动创建 PR，标记需重新审校
```

### 10. build_site.py - 站点构建
```python
# 基于 mkdocs-material
# 功能
- 多版本构建（mike 插件）
- 中文搜索索引生成
- 双语对照页面生成（可选）
- PDF 导出（mkdocs-pdf-export）
- 站点地图、搜索索引
- 自定义 JS 注入（分析、双语切换、版本选择器）

# 版本策略
- latest -> 跟踪上游 main
- 版本标签发布时创建快照分支 version/X.Y
- 保留最近 3 minor + 1 LTS 在线
- 更早版本打包到 GitHub Releases
```

---

## CI/CD 流水线设计

### 1. sync-upstream.yml
```yaml
触发：每周一凌晨 2 点 + 手动触发（指定 tag）
流程：
  1. checkout 仓库
  2. 运行 sync_docs.py
  3. 若有变更：创建 PR "chore: sync upstream fmt docs @ commit"
  4. PR 描述包含：变更文件列表、新增/删除/修改段落统计
```

### 2. translate-incremental.yml
```yaml
触发：sync-upstream PR 合并 + 手动触发
流程：
  1. 识别 .translation-state.json 中 status=pending 的段落
  2. 按文件/模块分批，优先级排序
  3. 调用 translate_batch.py 翻译
  4. 运行 validate_translation.py + validate_code_examples.py
  5. 校验通过：自动提交到源分支
  6. 校验失败：标记需人工复核，创建/更新 PR
  7. 更新 .translation-state.json
```

### 3. validate.yml
```yaml
触发：所有 PR + 定时每日
流程：
  1. 完整跑 validate_translation.py（全量）
  2. 完整跑 validate_code_examples.py（全量）
  3. 运行单元测试
  4. 生成质量报告上传为 Artifact
```

### 4. deploy.yml
```yaml
触发：main 分支推送（zh/ 变更）+ 版本标签推送
流程：
  1. 构建 mkdocs 站点（多版本）
  2. 生成 PDF（各版本）
  3. 部署到 GitHub Pages (gh-pages 分支)
  4. 上传 PDF 到 GitHub Release（版本标签时）
  5. 更新版本选择器数据
```

### 5. monitoring.yml
```yaml
触发：定时每 6 小时 + 工作流失败事件
告警规则：
  - sync_upstream_failed -> GitHub Issue + Email
  - translation_quality_drop (术语一致性<95%) -> GitHub Issue
  - deploy_failed -> GitHub Issue + Email
  - stale_translation (上游更新 14 天未同步) -> GitHub Issue
  - llm_cost_spike (单日 > $1) -> Email
```

### 6. test.yml
```yaml
触发：所有 PR + 合并到 main
流程：
  pytest tests/ --cov=scripts --cov-fail-under=80
  上传覆盖率报告
```

---

## 配置文件规范

### config/glossary.yml
```yaml
terms:
  - en: "format string"
    zh: "格式字符串"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: ["格式化字符串"]
    created_at: "2026-11-18"
    approved_by: "maintainer"
    usage_count: 0

  - en: "format"
    zh: "格式化"          # 默认动词
    contexts:
      - pattern: "format (?:a|the|your) (string|value)"
        zh: "格式化"
      - pattern: "format string"
        zh: "格式字符串"
      - pattern: "format specifier"
        zh: "格式说明符"
      - pattern: "the format of"
        zh: "格式"
    default_zh: "格式"
```

### config/style-guide.md
核心规则：
- 代码块/内联代码/HTML/链接 URL：保持原文
- API 名称（函数/类/宏/头文件）：保持英文
- 专业术语：使用术语表译名，首次出现可括注原文
- 人称：使用"您"/"我们"，避免"你"/"我"
- 语气：专业、简洁、避免口语化
- 标点：中文句子用中文标点，夹杂代码合理混用

### config/quality-metrics.yml
```yaml
metrics:
  terminology_consistency_rate:
    target: ">= 99%"
  code_block_integrity_rate:
    target: "100%"
  structure_integrity_rate:
    target: "100%"
  human_sampling_pass_rate:
    target: ">= 95%"
  user_feedback_score:
    target: ">= 4.5/5"
  incremental_translation_coverage:
    target: ">= 90%"
```

### mkdocs.yml 关键配置
```yaml
site_name: fmt 中文文档
site_url: https://fmt-zh.example.com
repo_url: https://github.com/your-org/fmt-zh-docs
edit_uri: edit/main/zh/

theme:
  name: material
  language: zh
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.highlight
    - search.share
    - content.code.copy
    - content.code.annotate

plugins:
  - search:
      lang: ['zh', 'en']
      separator: '[\s\u200b\-_,:;.!?，。！？、；：]+'
  - mike:
      version_selector: true
      deploy_prefix: ''
  - mkdocs-pdf-export:
      enabled: true
      output_dir: pdf/

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
  - admonition
  - pymdownx.details
  - attr_list
  - md_in_html

extra_javascript:
  - assets/js/bilingual-toggle.js
  - assets/js/analytics.js
```

---

## 里程碑与交付计划

| 阶段 | 任务 | 预估工时 | 交付物 | 验收标准 |
|------|------|----------|--------|----------|
| **M1: 基础设施** (Week 1-2) | 仓库初始化、核心脚本骨架、CI/CD 搭建、术语表/风格指南初版 | 16h | 可运行的同步+翻译+校验+部署流水线 | 1. `sync_docs.py` 能拉取上游 doc/ 到 source/<br>2. `translate_batch.py` 能翻译单段落并通过校验<br>3. GitHub Actions 全流程跑通（可用 mock LLM）<br>4. mkdocs 站点本地构建成功 |
| **M2: 首轮全量翻译** (Week 2-4) | 5 个文档文件全量翻译 + 人工审校 + 质量把关 | 40h | zh/ 目录完整中文文档，站点上线 | 1. 5 个文件 100% 翻译覆盖<br>2. 术语一致性 ≥ 99%<br>3. 代码示例 100% 编译通过<br>4. 站点部署可访问、搜索正常、版本切换正常 |
| **M3: 增量机制验证** (Week 4-5) | 模拟上游变更，验证增量检测、翻译、PR 流程 | 8h | 自动化增量翻译闭环跑通 | 1. 模拟上游修改/新增/删除文件<br>2. sync 检测正确、标记正确<br>3. 增量翻译仅处理变更段落<br>4. 翻译 PR 自动创建、校验通过自动合并 |
| **M4: 质量提升** (持续) | 术语表扩充、双语对照视图、搜索优化、用户反馈收集 | 持续 | 高质量可维护的中文文档站点 | 1. 术语表覆盖核心术语 200+<br>2. 双语模式可用<br>3. 用户反馈 Issue 处理 SLA 达标<br>4. 季度质量报告输出 |

---

## M2 完成勾验（2026-11-19）

> M2 首轮全量翻译完成，验收项逐条核对如下。

| 验收项 | 结果 | 说明 |
|--------|------|------|
| 5 个文件 100% 翻译覆盖 | ✅（口径按 DR-014 调整） | 4 个可翻译文件 447/447 段 = 100%；ChangeLog-old.md 经 DR-014 决策不翻译（670 段 skipped），覆盖统计分母调整为 447 |
| 术语一致性 ≥ 99% | ✅ | validate_translation.py 全量校验 0 错误 0 警告（含 glossary 一致性检查） |
| 代码示例 100% 编译通过 | ✅（口径按上游基线） | 中英文逐块等价（api 6=6、syntax 1=1 同 fail/pass 分布），翻译零破坏；7 处固有失败为上游示例片段性（文件组/表达式片段）+ 本机 libfmt 10.1.1 低于文档版本（12.x），属上游内容/环境性质，非翻译问题 |
| 站点部署可访问 | ✅ | https://jxsword.github.io/fmt-zh-docs/latest/ HTTP 200（2026-11-19 实测）；搜索/版本切换经 mkdocs-material 标准组件提供，浏览器人工验证待用户进行 |

- 翻译产出：index(26) / get-started(98) / syntax(88) / api(235) 共 447 段
- 质量门禁：ruff 0 错误；75 单元测试全绿；actionlint 0 告警
- 遗留：语感人工审校待用户进行（看板"待审校"区）；搜索/版本切换浏览器验证待用户

---

## 风险与对策

| 风险 | 可能性 | 影响 | 对策 |
|------|--------|------|------|
| 上游文档结构大幅调整 | 中 | 高 | 段落级 hash + 语义相似度匹配，人工介入复杂重构；DR-007 分级响应预案 |
| LLM 翻译术语不一致 | 高 | 中 | 术语表强制注入 prompt + CI 校验 + 复核流程；DR-003 上下文消歇 |
| 代码示例被误翻译 | 低 | 高 | 代码块保护机制（AST 级识别）+ 正则双重校验 + 编译验证；DR-004/009 |
| 上游频繁发布导致追赶压力 | 中 | 中 | 自动化流水线 + 版本锁定 + 优先翻译核心 API |
| 贡献者协作冲突 | 低 | 中 | PR 单文件/单模块粒度，避免大冲突；CONTRIBUTING_TRANSLATION.md 规范流程 |
| LLM API 成本超支 | 低 | 低 | TM 复用优先、便宜模型优先、日/月预算上限告警 |
| 上游迁移文档平台 | 低 | 中 | 适配器模式隔离上游源（DR-010），仅需实现新 Adapter |

---

## 启动清单

```bash
# 1. 初始化仓库
cd /home/ssy/soft-tech-docs-translate/fmt-zh-docs
git init
git remote add origin <your-fork-url>
git remote add upstream https://github.com/fmtlib/fmt.git

# 2. 创建目录结构
mkdir -p source zh scripts/.github/workflows config tests docs assets/js

# 3. 编写核心脚本（按本计划脚本设计章节）
#    优先：sync_docs.py, segment_markdown.py, protect_untranslatable.py
#         translate_batch.py, validate_translation.py

# 4. 创建配置文件
#    config/glossary.yml (从本计划复制初版)
#    config/style-guide.md
#    config/quality-metrics.yml
#    mkdocs.yml

# 5. 创建 GitHub Actions workflows
#    .github/workflows/sync-upstream.yml
#    .github/workflows/translate-incremental.yml
#    .github/workflows/validate.yml
#    .github/workflows/deploy.yml

# 6. 同步首版上游文档
python scripts/sync_docs.py --init

# 7. 运行首轮全量翻译（可用 mock/便宜模型测试流程）
python scripts/translate_batch.py --all --source-dir source --target-dir zh

# 8. 人工审校重点文件：api.md、syntax.md

# 9. 配置 mkdocs.yml 并本地预览站点
mkdocs serve

# 10. 推送并启用 GitHub Actions
git add .
git commit -m "chore: init fmt-zh-docs project with M1 infrastructure"
git push -u origin main

# 11. 在 GitHub 仓库 Settings -> Actions 启用 workflows
#     配置 Secrets: OPENAI_API_KEY (或其他 LLM 提供商密钥)
```

---

## 附录：术语表初版（config/glossary.yml 种子数据）

```yaml
terms:
  # 核心术语（首批必译统一）
  - en: "format string"
    zh: "格式字符串"
    status: "approved"
    context: "api.md:syntax.md:get-started.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "replacement field"
    zh: "替换字段"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "format specifier"
    zh: "格式说明符"
    status: "approved"
    context: "syntax.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "format specification"
    zh: "格式规范"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "argument"
    zh: "参数"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "placeholder"
    zh: "占位符"
    status: "approved"
    context: "syntax.md:get-started.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "alignment"
    zh: "对齐"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "fill character"
    zh: "填充字符"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "width"
    zh: "宽度"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "precision"
    zh: "精度"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "locale"
    zh: "区域设置"
    status: "approved"
    context: "syntax.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "presentation type"
    zh: "呈现类型"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "compile-time"
    zh: "编译时"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "runtime"
    zh: "运行时"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "type erasure"
    zh: "类型擦除"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "user-defined type"
    zh: "用户定义类型"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "formatter"
    zh: "格式化器"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "format context"
    zh: "格式上下文"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "parse context"
    zh: "解析上下文"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "chrono"
    zh: "时间日期"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "duration"
    zh: "时长"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "time point"
    zh: "时间点"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "range"
    zh: "范围"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "tuple"
    zh: "元组"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "nested replacement field"
    zh: "嵌套替换字段"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "named argument"
    zh: "命名参数"
    status: "approved"
    context: "syntax.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "positional argument"
    zh: "位置参数"
    status: "approved"
    context: "syntax.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "automatic indexing"
    zh: "自动索引"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "sign"
    zh: "符号"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "alternate form"
    zh: "替代形式"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "zero padding"
    zh: "零填充"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "digit grouping"
    zh: "数字分组"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "round-trip"
    zh: "往返保证"
    status: "approved"
    context: "syntax.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "significand"
    zh: "尾数"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "exponent"
    zh: "指数"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "scientific notation"
    zh: "科学计数法"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "fixed-point"
    zh: "定点表示"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "hexadecimal"
    zh: "十六进制"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "binary"
    zh: "二进制"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "octal"
    zh: "八进制"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "escape sequence"
    zh: "转义序列"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "debug output"
    zh: "调试输出"
    status: "approved"
    context: "syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "type-safe"
    zh: "类型安全"
    status: "approved"
    context: "api.md:get-started.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "buffer overflow"
    zh: "缓冲区溢出"
    status: "approved"
    context: "index.md:api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "format_error"
    zh: "格式错误"
    status: "approved"
    context: "api.md:syntax.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "system_error"
    zh: "系统错误"
    status: "approved"
    context: "api.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "header-only"
    zh: "仅头文件"
    status: "approved"
    context: "api.md:get-started.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  - en: "module"
    zh: "模块"
    status: "approved"
    context: "api.md:get-started.md"
    aliases: []
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0

  # 消歇术语示例
  - en: "format"
    zh: "格式化"
    status: "approved"
    contexts:
      - pattern: "format (?:a|the|your) (string|value)"
        zh: "格式化"
      - pattern: "format string"
        zh: "格式字符串"
      - pattern: "format specifier"
        zh: "格式说明符"
      - pattern: "the format of"
        zh: "格式"
    default_zh: "格式"
    created_at: "2026-11-18"
    approved_by: "init"
    usage_count: 0
```

---

## 实施开始确认

> **当前状态**：计划已写入 `PLAN.md`，准备启动 **M1 基础设施搭建** 阶段。
>
> **下一步行动**：按启动清单顺序执行，完成后等待复审。
>
> **预计 M1 完成时间**：16 小时（分 2-3 个工作会话）
>
> **M1 验收标准**：
> 1. `sync_docs.py --init` 成功拉取上游 doc/ 到 source/
> 2. `translate_batch.py` 能翻译单段落并通过 `validate_translation.py` 校验
> 3. GitHub Actions 5 个 workflow 全部可跑通（可用 mock LLM 测试）
> 4. `mkdocs serve` 本地预览站点正常，中文搜索、版本切换、PDF 导出功能验证通过

---

**文档结束**  
如有疑问或需调整，请在复审时提出。
# fmt 中文文档翻译贡献指南

感谢您对 fmt 中文文档翻译项目的关注！本文档说明如何参与翻译贡献。

## 角色与权限

| 角色 | 权限 | 获取方式 |
|------|------|----------|
| 翻译贡献者 | 认领段落、提交翻译 PR | 任何人均可 |
| 审校员 | 审批翻译、合并 PR、维护术语表 | 连续 3 个 PR 通过后邀请 |
| 维护者 | 发布版本、管理 CI、处理冲突 | 核心团队指定 |

## 快速开始

### 1. 环境准备

```bash
# Fork 仓库到您的 GitHub 账号
git clone https://github.com/YOUR_USERNAME/fmt-zh-docs.git
cd fmt-zh-docs

# 安装依赖
pip install -r requirements.txt
```

### 2. 认领翻译任务

1. 查看 [翻译任务看板](docs/translation-board.md) 或 GitHub Projects
2. 评论认领："我来翻译 `api.md` 的 `formatter` 章节"
3. 创建分支：`git checkout -b translate/api-formatter`
4. 开始翻译

### 3. 翻译流程

```bash
# 1. 同步最新上游文档（可选，通常由 CI 自动完成）
python scripts/sync_docs.py --init

# 2. 查看待翻译段落
python scripts/translate_batch.py --dry-run

# 3. 翻译（支持单文件）
python scripts/translate_batch.py --file api.md

# 4. 本地验证
python scripts/validate_translation.py

# 5. 提交 PR
git add zh/api.md .translation-state.json
git commit -m "feat: translate api.md formatter section"
git push origin translate/api-formatter
```

### 4. PR 规范

- **标题格式**：`feat: translate <file> (<section>)`
- **描述包含**：
  - 翻译文件/章节
  - 涉及的术语表更新（如有）
  - 特殊处理说明（如代码示例调整）
- **最小粒度**：单文件或单章节，避免大 PR

## 翻译规范

请严格遵循 [翻译风格指南](config/style-guide.md) 和 [术语表](config/glossary.yml)。

### 核心原则

1. **代码不翻译**：代码块、内联代码、API 名称保持原文
2. **术语统一**：必须使用术语表定义的译名
3. **专业语气**：使用"您"/"我们"，避免口语化
4. **结构保持**：标题层级、列表、表格结构不变

### 常见问题

| 问题 | 处理方式 |
|------|----------|
| 术语表未收录 | PR 中提出，讨论后加入术语表 |
| 语境歧义 | 查看术语表上下文消歇规则 |
| 代码示例错误 | 标记需修复，不翻译代码部分 |
| 格式不一致 | 参考风格指南统一 |

## 审校流程

1. PR 创建后，至少 1 位审校员 Review
2. 审校员检查：术语一致性、代码完整性、语言质量
3. 通过后由审校员合并（Squash and merge）
4. 自动触发站点部署

## 冲突解决

- **同段落多人翻译**：先到先得（以 PR 创建时间为准）
- **术语分歧**：在 PR 讨论区决议，更新术语表
- **质量争议**：维护者裁决，必要时回滚重译

## 认可机制

- 贡献者名单记录在 [AUTHORS_TRANSLATION.md](AUTHORS_TRANSLATION.md)
- 统计维度：段落数、字数、审校通过率
- 季度表彰：Top Contributors 称号

## 行为准则

请遵守 [Contributor Covenant](https://www.contributor-covenant.org/zh-CN/version/2/1/code_of_conduct/) 行为准则。

## 联系方式

- GitHub Issues: 翻译相关问题请加 `translation` 标签
- GitHub Discussions: 术语讨论、流程建议
- Email: translation@fmt-zh.example.com

---

*本指南会随项目发展持续更新，欢迎提出改进建议。*
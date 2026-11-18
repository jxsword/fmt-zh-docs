# fmt 中文文档质量报告（2026 Q4 首版）

> 生成日期：2026-11-19 ｜ 覆盖周期：M1~M4 初期（2026-11-18 至 2026-11-19）
> 生成方式：会话内人工汇总（M4 后续由 monitoring workflow 自动化产出）

## 1. 翻译覆盖

| 文件 | 段落 | 状态 |
|------|------|------|
| index.md | 26 | 100% 翻译 + 校验通过 |
| get-started.md | 98 | 100% 翻译 + 校验通过 |
| syntax.md | 88 | 100% 翻译 + 校验通过 |
| api.md | 235 | 100% 翻译 + 校验通过 |
| ChangeLog-old.md | 670 | 不翻译（DR-014，skipped） |
| **合计（可翻译口径）** | **447** | **100%（447/447）** |

## 2. 自动校验

- validate_translation.py 全量：**0 错误 0 警告**（术语一致性/代码块完整性/
  结构完整性/内联代码/链接/占位符/HTML 标签全项通过）
- 机翻痕迹模式扫描：0 命中
- 语感人工审校：进行中（看板"待审校"区，用户执行）

## 3. 代码示例完整性

- 中英文逐块编译等价验证：api 6=6、syntax 1=1（同 fail/pass 分布）——**翻译零破坏**
- 7 处固有失败归因：上游示例片段性（文件组/表达式片段）+ 本机 libfmt 10.1.1
  低于文档对应版本（12.x），非翻译问题
- 系统已装 libfmt-dev 10.1.1，CI 环境 validate_code_examples 带 `|| true` 不阻塞

## 4. 术语表

- 条目数：**233**（M4 扩充：52 → 233，+181，达 PLAN 验收 200+ 目标）
- 扩充方法：source 高频短语提取 → 与校验器同逻辑预检（en 出现⇒zh 必须在译文，
  12 处冲突按译文实际用词修正：备用表示/格式 API/旧式编译时检查/动态库等）→
  verified 54 + dictionary 118 + 修正 9
- 全量校验在扩充后仍 0 警告（预检与校验器逻辑对齐保证）

## 5. CI/CD 状态（截至 2026-11-19）

| Workflow | 状态 | 备注 |
|----------|------|------|
| Run Tests（test/lint/type-check） | ✅ | 75 测试全绿；ruff 0 错误 |
| Validate Translations | ✅ | 翻译校验硬门禁 |
| Sync Upstream Documentation | ✅ | blobless clone 真机验证 |
| Deploy Chinese Site | ✅ | mike → gh-pages → Pages |
| Incremental Translation | ✅ | NVIDIA_API_KEY secret 已配置 |
| Monitoring & Alerts | ✅ | 表达式语法修复后真机通过 |

站点：https://jxsword.github.io/fmt-zh-docs/latest/ （HTTP 200 实测）

## 6. 增量机制（M3）

- sync_docs.py --tag/--since/--dry-run 全部可用；A/M/D/R 增量处理 + 段落状态
  hash 迁移 + 归档不删历史 + 幂等重跑
- 模拟全链路实测：kept_translated=3 实证增量翻译仅处理变更段落
- 报告：docs/m3-incremental-verification.md

## 7. 双语模式（DR-005）

- 独立对照页已落地：zh/bilingual/ 四页 + 说明页，447 段逐位对齐（0 错位）
- 悬浮提示模式：bilingual-toggle.js 就位，依赖构建期原文注入（未实现），
  当前以对照页模式为准

## 8. 反馈闭环（DR-008）

- Issue 模板已建：translation-feedback.yml（SLA 分级下拉 + 页面定位）
- SLA：代码/结构 24h、术语 48h、一般 1 周、首次响应 2 工作日

## 9. 技术债与后续计划

| 项 | 现状 | 计划 |
|----|------|------|
| 测试覆盖率 | **81.85%（门槛 80%，129 测试）✅ M4 达成** | 持续保持；protect_untranslatable 56% 为下期补测重点 |
| black 格式统一 | 未启用 | M4 专项全库格式化后启用 CI 检查 |
| monitoring 滞后天数 | 占位 0 | state 加同步时间戳后计算真实天数 |
| 语感人工审校 | 待用户 | 看板"待审校"区闭环 |
| 悬浮双语模式 | 依赖原文注入 | 构建期 data-original 注入方案评估；对照页模式已可用 |

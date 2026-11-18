# M3 增量机制验证报告（2026-11-19）

> 任务 4（M3 增量机制验证）产出。模拟上游变更全链路实测记录。

## 1. 验证设计

- **隔离工作区**：`/tmp/fmt-m3-sim/`（复制 scripts/ + config/，REPO_ROOT 天然隔离，不污染真仓库）
- **Mock 上游**：`/tmp/fmt-m3-sim-upstream/`（本地 git 仓库，file:// 注入 `--repo` 参数）
- **环境真实口径**：sync_docs.py 生产 CLI 全程真实调用（非单测 mock）

## 2. 全链路实测记录

| 环节 | 操作 | 实测结果 |
|------|------|----------|
| 1. 全量同步 | `sync_docs.py --init --repo file:///tmp/fmt-m3-sim-upstream` | 8 段全部 pending，state 写入正常 |
| 2. M2 已完成态模拟 | 8 段置 translated + zh/ 初版翻译 | pending 0 / translated 8 |
| 3. 上游变更 | index.md 修改 1 段（M）+ 新增 range.md（A） | commit `13dc4634` |
| 4. 增量同步 | `sync_docs.py --since <c0> --repo file://…` | **index.md M：added 1 / removed 1 / kept_translated 3**；range.md A：3 段 pending |
| 5. 增量翻译 | 仅处理 4 个 pending 段（index 1 + range 3），3 段未动翻译保留 | zh/index.md 单段替换、zh/range.md 新建 |
| 6. 状态流转 | pending → translated（带 translator/translated_at 元数据） | pending 0 / translated 11，计数守恒（8+4-1） |
| 7. 校验闭环 | validate_translation.py --file ×3 | 0 错误 0 警告 |

## 3. PLAN M3 验收对照

| 验收项 | 结果 |
|--------|------|
| 1. 模拟上游修改/新增/删除文件 | ✅ 单测覆盖 M/A/D/R 全类型（21 例）+ 模拟实测 M/A |
| 2. sync 检测正确、标记正确 | ✅ added/removed/kept_translated 统计准确；幂等性单测覆盖 CI 重跑场景 |
| 3. 增量翻译仅处理变更段落 | ✅ 实证 kept_translated=3，仅 4 段进入翻译队列 |
| 4. 翻译 PR 自动创建、校验通过自动合并 | ◐ 部分验证：sync-upstream workflow 真机 success（无变更路径）；PR 自动创建分支依赖上游实际变更，待首次真实上游更新触发完整闭环；真仓库 PR+CI 闭环另经手工 PR 验证（见第 4 节） |

## 4. 真仓库 PR + CI 闭环（同日验证）

- 分支 `m3-verification` → 推 origin → PR → validate.yml + test.yml（PR 触发）→ 合并
- 结论：PR 触发的 CI 闭环真机可用

## 5. 遗留与后续

- **NVIDIA_API_KEY secret 未配置**（用户操作）：translate-incremental workflow
  在 PR 含 source/** 变更时才会触发自动翻译；key 配好后 M3 PR 闭环全自动化
  （sync 建 PR → translate-incremental 翻译提交 → validate → merge）
- 本机 libfmt 10.1.1 低于文档版本（12.x）：syntax.md:625 一类示例失败属环境版本差异，
  CI（无 libfmt）中 validate_code_examples 带 `|| true` 不阻塞
- `/tmp` 模拟工作区为一次性验证环境，不入库

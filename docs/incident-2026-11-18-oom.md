# 事故记录：2026-11-18 OOM 内存耗尽导致会话/应用异常退出

> 记录：2026-11-19 ｜ 关联决策：DR-011 ｜ 影响脚本：`scripts/sync_docs.py`

## 1. 事故经过

M1 基础设施搭建期间，会话运行 `python3 scripts/sync_docs.py --init --dry-run`（23:23:17 启动）。
脚本完成 git sparse fetch 与文件读取（stdout 已打印 `Files: [...]`）后进入 `segment_md()` 分段，
因死循环 bug 在 2 分 36 秒内把内存吃到 **anon-rss 12.4 GB + swap 2.2 GB**（虚拟内存 20.9 GB）：

- 23:25:17 ZCode 120 秒超时，把进程移入后台（之后 stdout 再无输出，`State saved` 未出现）
- 23:25:53 内核全局 OOM 击杀 python3 (pid 13470)，整机内存一度接近占满（gnome-shell 自身分配失败）
- 同一秒 ZCode 扩展宿主连接断开，主进程走 forceQuit 有序退出（exitCode 0，非崩溃）
- 23:34 用户重启 ZCode

## 2. 根因（segment_md 段落分支死循环）

`sync_docs.py` 修复前的段落分支：内层循环遇到以 `<` 开头的行会立即 `break`，而外层
**没有兜底的 `i += 1`**，于是对同一行无限生成空 `Segment` 对象（每秒约 13 万个，
156 秒 ≈ 2000 万个 ≈ 12.4 GB）。

触发条件：**行以 `<` 开头且同行没有 `>`** —— 不满足 html 分支的
`st.startswith('<') and '>' in st`，落入段落分支。实际触发行（首次 fetch 的上游文档）：

- `source/api.md:170`、`source/get-started.md:116`、`source/get-started.md:127`：跨行 HTML 注释 `<!-- ...`
- `source/index.md:96`：`<a href='`（属性跨行）

## 3. 已实施的修复（DR-011）

1. **防死循环护栏**：段落分支追加 `if i == start: i += 1`，杜绝任何"未推进"情形。
2. **html 分支放宽**：`st.startswith('<')` 即按 HTML 块消费到空行，跨行注释整块正确捕获。

离线验证（不联网）：source/ 全部 5 个文件共 **1117 段无死循环**，
`api.md:170` 正确捕获为 html_block（行 170–171）。

## 4. 防复发加固（本机级）

- **memgate 内存闸**（`~/.local/bin/memgate`）：会话内运行长任务/内存不可预估脚本一律包裹，
  `memgate [上限MB] <cmd>`，缺省 4G。经 systemd 瞬态 scope 施加 cgroup MemoryMax，
  失控只损失被限进程。已实测：200MB 上限下申请 1GB 随机内存，进程被击杀（exit 137）。
- **earlyoom 1.9.0**（系统级，已启用）：内存余量 ≤10% 发 SIGTERM、≤5% 发 SIGKILL 给最大进程，
  在内核 OOM 之前温和干预，避免整机僵死连带应用退出。

## 5. 对续跑 M1 的具体影响

- `source/*.md` 5 个文件是崩溃那次运行写入的（内容完整）；`.translation-state.json`
  **未生成**（`State saved` 未出现）。重新执行 `--init` 即可覆盖 source 并写入状态文件。
- 注意：脚本当前不解析命令行参数，`--dry-run` 标志无实际作用（main() 直接执行 sync_init）。
- 续跑纪律：`memgate python3 scripts/sync_docs.py --init`。

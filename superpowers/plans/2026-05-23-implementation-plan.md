# 实施计划：2026-05-23

> 总工期：1 天（已完成）
> 开发者：joe-qai
> 任务数：4 大项 / 18 文件变更

---

## 执行流程

### Phase 1: 脚本执行器重构（3 文件）

```
backend/executors/script_executor.py
├── start()       # 启动子进程 + 行级输出捕获
├── wait()        # 等待结束 + 可取消 + 结果组装
├── cancel_check  # 回调检测，每行输出后调用
├── run_script()  # → start() + wait() 代理
└── run()         # 统一入口（Query Script → start → wait）

backend/core/task_dispatcher.py
├── _execute_on_device → Popen 后立即 push active_processes
├── cancel_task → terminate → wait(5s) → kill 兜底
└── 状态传播 → "cancelled"

backend/api/tasks.py
├── 取消 endpoint
└── 顺序 ID (task_1, task_2…)
```

**验证**：`pytest backend/tests/ -v` 全绿

### Phase 2: 前端 UI 统一（13 文件）

```
新文件:
  frontend/src/utils/format.js        → formatDate()
  backend/core/id_generator.py         → next_id()

视图修改（icon 替换 + formatDate slot）:
  Projects.vue          Eye, Stop, Check, Delete
  Reports.vue           Eye, Download, Delete
  ScriptManagement.vue  Edit, Download, Delete
  Tasks.vue             Redo, Close, Delete
  Devices.vue           Disonnect, Reload, Link, Minus
  Keywords.vue          Edit, Delete
  POManagement.vue      Edit, Copy, Delete
  APKManagement.vue     Delete
  TestCaseManagement.vue Edit, Delete
  ProjectDetail.vue     formatDate 仅
  Debug.vue             工具栏精简 + iframe 双状态 + 云 URL
```

**验证**：`cd frontend && npm run build` 通过

### Phase 3: 在线调试优化（3 文件）

```
Debug.vue
├── @change 移除
├── loadRoot / refreshIframe 移除
├── currentIframeSrc → 仅返回云 URL
├── iframe placeholder 双状态
└── loadDevice → device.platform

uiautodev_manager.py
├── start() → uiauto.dev → python -m uiautodev 回退
├── stop() → taskkill /F /IM uiauto*
├── get_status → cloud URL
└── get_device_url → platform 参数

test_uiautodev_manager.py
└── 断言适配
```

**验证**：`pytest backend/tests/test_uiautodev_manager.py -v` 通过

### Phase 4: 清理 & 提交

```
git add --all
git diff --cached --stat   → 确认仅含计划内文件
git commit -m "feat: sprint-3 任务调度重构+UI统一+在线调试优化"
git push origin main
```

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| Debug.vue 编码损坏 | 用 Python 写 .py 脚本执行编辑，避免 PowerShell 引号转义问题 |
| vite.config.js 被 `git checkout` 恢复 | 确认 `proxy` 目标为 `uiauto2.devsleep.com` |
| 子进程杀不干净 | `taskkill /F /IM uiauto*` 覆盖所有派生进程 |

## 已完成确认

- [x] `git status` 显示 18 modified + 2 new files
- [x] `git log --oneline -20` 确认 sprint 3 的提交基线为 `c8e3d7f`
- [x] 在 `superpowers/specs/` 记录了完整变更规格
- [x] 在 `superpowers/plans/` 记录了实施过程

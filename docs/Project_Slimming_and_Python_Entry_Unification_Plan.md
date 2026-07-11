# 项目瘦身与 Python 入口统一路径

## 1. 目的

本文只规划两个范围明确、可以保持模拟结果不变的阶段：

1. 清理可再生成的冗余输出，并建立稳定的输出保留和清理规则。
2. 统一 Python 的日常运行入口、包结构和导入方式。

经营历史、有效客流预测和玩家事务的界面合并不在本文范围内。该工作继续单独记录在 `Post_Refactor_UI_Consolidation_Plan.md`，等本轮瘦身和 Python 入口稳定后再处理。

## 2. 当前判断

项目目前没有两份 Python 源码，也没有项目内的两套虚拟环境。电脑上虽然同时安装 Python 3.13 和 Python 3.10，但项目现已收敛到单一支持版本：

- Python 3.13 是唯一支持的运行和测试版本。
- Python 3.10 可以继续存在于电脑中，但不再用于本项目运行或兼容测试。

无需卸载电脑中的 Python 3.10；统一的含义是项目元数据、启动入口和 CI 均只面向 Python 3.13，不再维护重复的版本兼容测试。

当前真正占空间的是生成结果：

- `output/` 约 650 MB，其中 Seed Explorer 缓存约 460 MB。
- 历史错误路径 `airport/airport/output/` 约 94 MB。
- 多个早期手工测试、探针和命令行验证目录仍留在正式 `output/` 下。
- 源码、配置、文档和前端文件合计远小于生成结果，不应为了表面上的文件数量盲目删除。

## 3. 不变约束

两个阶段都必须遵守：

- 不修改模型公式、默认参数、随机数消费顺序和浮点计算顺序。
- 不删除 `saves/` 中的玩家存档。
- 不删除当前 Manifest 指向的 Viewer release。
- 不删除正在运行、正在生成或被锁定的 Run。
- 不把缓存清理和存档清理放进同一个操作。
- 所有删除操作先提供预览；默认采用显式确认，不进行静默递归删除。
- 每个结构性步骤都运行 Python 3.13 全套测试和关键页面浏览器验收。
- 固定 Seed 的 API 快照和数值摘要必须保持不变。

## 4. 目标目录关系

完成后继续维持以下职责边界：

```text
airport/
  airport_sim/             正式模型与命令入口
  airport_ui/              本地 8776 服务入口
  config/                  正式配置
  static/                  前端静态资源
  schemas/                 API 和输出 Schema
  tests/                   自动化测试
  output/                  可再生成结果
    seed_explorer_runs/    动态测试缓存
    macro_runs/            完整宏观 Run
    viewer_releases/       已发布 Viewer 版本
  saves/                   不可随缓存一起删除的玩家存档
    seed_explorer/
```

`airport/airport/output/` 不属于目标结构。确认其中没有唯一需要保留的 Run 后，应从工作区移除。

## 5. 阶段一：输出瘦身与生命周期统一

### 5.1 建立只读盘点

先实现统一的输出盘点，至少列出：

- 目录类别、大小、文件数和最后修改时间。
- Seed、年份、模型指纹和缓存是否仍有效。
- 当前 Viewer Manifest 引用的 release。
- 当前保存槽位引用的 Seed。
- 活动任务、运行锁和 staging 目录。
- 可安全删除、需要确认、禁止删除三种状态。

盘点命令只读取文件，不修改工作区。建议目标命令：

```powershell
python -m airport_sim cache list
python -m airport_sim cache plan
```

在 `airport_sim` 包尚未建立前，可以先由现有服务模块提供相同函数，阶段二再迁入正式命令入口。

### 5.2 审计旧嵌套输出

对 `airport/airport/output/` 做一次性审计：

1. 读取其中的 Run Manifest、Seed、年份和生成时间。
2. 与正式 `output/` 中的 Run 比较，不只比较文件名。
3. 唯一且仍有保留价值的 Run 先迁移到正式目录，并重新通过输出校验。
4. 已重复或明确属于旧 smoke/test 的产物列入清理计划。
5. 审计结果写入日志；确认后再删除旧嵌套目录。

不得直接把整个目录移动到正式 `output/`，以免覆盖较新的结果或破坏 Manifest。

### 5.3 清理历史测试产物

正式 `output/` 中名称带有 `test`、`smoke`、`probe`、`draft` 或临时检查含义的旧目录，不能仅凭名称删除。应先确认：

- 当前测试代码不再引用该固定路径。
- 目录不被当前 Viewer Manifest 引用。
- 目录不是玩家存档来源。
- 目录没有活动锁或未完成 staging 标记。

确认后统一清理。后续自动化测试必须优先使用系统临时目录或测试专用临时根目录，并在测试结束时清除，避免再次污染正式 `output/`。

### 5.4 Seed 缓存保留策略

当前 Seed Explorer 默认最多保留 4 个完整 Run。改为可配置策略：

- 默认保留最近 2 个有效 Run。
- 当前正在浏览、运行或被任务锁定的 Run 不清理。
- 玩家存档只保存行动和当前状态，不因对应缓存删除而丢失；需要时可按同一 Seed 重算。
- 可以按 Seed 显式固定某个 Run，使自动清理跳过它。
- 清理前显示预计释放空间。

保留数量属于缓存策略，不得进入模型指纹，也不得改变固定 Seed 结果。

### 5.5 清理命令的安全边界

建议提供：

```powershell
python -m airport_sim cache plan
python -m airport_sim cache clean
python -m airport_sim cache clean --confirm
```

规则：

- `plan` 永远只预览。
- 普通 `clean` 再次显示计划并要求确认。
- 自动化环境才允许显式 `--confirm`。
- 所有目标必须解析为 `output/` 内的绝对路径。
- 禁止接受任意外部路径作为递归删除目标。
- 每次清理输出删除目录、释放字节数和跳过原因。
- 清理失败时继续保护未处理目录，不留下半迁移状态。

本地首页可以以后增加“查看缓存”入口，但本阶段不要求重做界面。

### 5.6 减少同一 Run 的重复大文件

有效客流预测已经支持按报告加载数据块，但完整 Run 中仍可能同时保留旧式完整 Viewer JS 和按需数据块。处理顺序：

1. 先记录 API、独立 Viewer、Viewer 发布和回退路径分别读取哪些文件。
2. 给输出校验增加“动态测试缓存”和“正式 Viewer 发布”两类 profile。
3. 动态测试缓存只生成 API 和模拟重算真正需要的文件。
4. 正式 Viewer 发布继续生成或复制其兼容回退所需文件。
5. 浏览器、API 快照和固定 Seed 测试全部通过后，才取消缓存内的重复完整文件。

这一步属于阶段一中风险最高的子项，应在普通缓存清理稳定后单独实施。

### 5.7 阶段一验收

- `saves/` 文件数量、内容和存档加载结果不变。
- 当前 Viewer release 可继续访问。
- 8776 首页、Seed Explorer、全球宏观、北京经营和有效客流预测均可打开。
- 清理前后相同 Seed 重算得到相同 API 快照和数值摘要。
- 测试运行不再在正式 `output/` 留下固定名称的测试目录。
- `airport/airport/output/` 完成审计后不存在。
- 默认只保留最近 2 个未固定 Seed 缓存。
- 清理命令不能越过 `output/`，也不能删除活动 Run、当前 release 或玩家存档。

### 5.8 阶段一回退

- 在删除旧嵌套输出前，先把唯一 Run 移入一个工作区外的临时备份目录。
- 缓存保留数量可以立即恢复为 4，不影响存档和模型。
- 重复大文件优化必须以独立提交进行；出现 Viewer 回退问题时恢复旧输出 profile。
- 不依赖恢复已删除缓存来保证玩家状态；缓存始终应能由 Seed 和行动日志重算。

## 6. 阶段二：Python 入口与包结构统一

### 6.1 版本策略

- README、Windows 启动脚本和本地开发说明统一使用 Python 3.13。
- `pyproject.toml` 声明 `requires-python = ">=3.13,<3.14"`，明确锁定 3.13 系列。
- CI 只在 Python 3.13 上验证，继续保留 Windows/Linux 两个平台覆盖。
- Python 3.10 不再属于项目支持范围，也不再形成重复测试任务。
- 项目不提交虚拟环境、解释器或第三方依赖副本。

### 6.2 建立正式 `airport_sim` 包

目标入口：

```powershell
python -m airport_sim run --seed 20261324
python -m airport_sim serve
python -m airport_sim validate-config
python -m airport_sim cache list
python -m airport_sim cache plan
python -m airport_sim cache clean
```

建议职责：

```text
airport_sim/
  __init__.py
  __main__.py
  cli.py
  paths.py
  commands/
    run.py
    serve.py
    validate_config.py
    cache.py
```

命令层只解析参数和调用现有模型/服务函数，不在第一轮迁移时重写计算模块。

### 6.3 先统一路径，再统一导入

第一步把项目根目录、配置目录、输出目录、Schema 目录和存档目录集中到 `airport_sim.paths`。保留现有常量作为薄包装，确保调用结果相同。

第二步将模型统一通过包导入，逐步消除：

- `if __package__` 下的两套重复 import。
- 为直接脚本运行准备的顶层模块 import。
- `sys.path.insert(...)` 注入。
- 各模块自行推导但语义相同的项目根路径。

每次只迁移一个入口或一组强相关模块。不得在同一步顺便调整模型函数、参数默认值或输出格式。

### 6.4 兼容旧入口

以下旧入口暂时保留为薄包装：

- `start_airport_ui.bat`
- `dynamic_tests/seed_explorer/start_seed_explorer.bat`
- `python -m airport_ui`
- 已记录在文档中的主要模型脚本命令

薄包装只转发到新命令并显示迁移提示，不复制实现。至少经过一个稳定周期和一次完整固定 Seed 验收后，再决定是否删除旧模型脚本入口。

对普通使用者，唯一推荐方式逐步收敛为：

```powershell
python -m airport_sim serve
```

Windows 双击入口仍可以保留，因为它解决的是易用性，不属于有害冗余。

### 6.5 `pyproject.toml` 与安装方式

补齐包发现和命令声明，使以下方式可用：

```powershell
python -m pip install -e .
airport-sim serve
```

但可编辑安装不能成为运行源码的唯一前提；在项目根目录使用 `python -m airport_sim` 必须仍然工作。运行依赖继续保持标准库优先，新增第三方依赖必须有明确收益。

### 6.6 测试迁移顺序

1. 先为新 CLI 增加参数解析和路径测试。
2. 验证从项目根目录、父目录和任意工作目录启动时落到同一个输出根。
3. 验证新旧入口对同一 Seed 生成一致 Manifest、CSV 摘要和 API 快照。
4. 把内部测试逐步改为导入 `airport_sim`，同时保留旧入口契约测试。
5. 新入口稳定后删除重复 import 分支。
6. 最后更新 README 和架构事实文档，将旧命令移到兼容说明。

### 6.7 阶段二验收

- 普通用户只需要知道 `python -m airport_sim serve`。
- Windows 双击启动仍然可用，并调用同一实现。
- 从任意工作目录运行都使用同一配置、输出、存档和 Schema 根目录。
- 不再依靠 `sys.path.insert(...)` 启动服务。
- 主调度器不再保留两套大段重复 import。
- Python 3.13 全套测试通过。
- 新旧入口对固定 Seed 的输出结果一致。
- 8776 服务身份、端口保护、本地来源检查和停止脚本行为不变。

### 6.8 阶段二回退

- 新 CLI 在稳定前只作为现有入口的并行入口，不立即删除旧命令。
- 包迁移按模块分步进行，旧模块在完成对等验证前保留薄包装。
- 任一固定 Seed 或 API 快照不同，立即停止后续迁移并恢复该步导入路径。
- Python 最低版本已统一到 3.13；版本回退不再属于本项目的常规验收范围。

## 7. 推荐实施顺序

```text
只读空间盘点
  -> 旧嵌套输出审计
  -> 历史测试产物清理
  -> 安全清理命令
  -> Seed 缓存可配置保留
  -> 测试输出临时化
  -> Run 重复大文件评估与精简
  -> 建立 airport_sim CLI 壳层
  -> 集中路径定义
  -> 逐步统一包导入
  -> 旧入口变为薄包装
  -> 更新唯一运行事实文档
```

前六步主要降低磁盘和维护负担；后五步降低启动和代码结构复杂度。两组工作不要交叉修改模型公式。

## 8. 本轮完成标准

当以下条件全部满足，可以认为第一、第二阶段完成：

- 工作区不再存在旧嵌套输出目录。
- 正式输出、临时缓存、Viewer 发布和玩家存档具有明确且不同的生命周期。
- 可预览并安全清理缓存，默认不保留无上限历史结果。
- 测试不再污染正式输出目录。
- 同一 Run 不再无必要地保存多份等价大文件。
- 日常运行统一推荐 Python 3.13 和 `python -m airport_sim serve`。
- Python 3.13 是唯一运行与测试目标，不形成第二套版本测试流程。
- 新旧兼容入口共用同一实现。
- 固定 Seed、API、Viewer 和玩家存档行为保持不变。

完成这些工作后，再根据 `Post_Refactor_UI_Consolidation_Plan.md` 单独评估第三阶段的界面合并。

## 9. 实施结果（2026-07-11）

第一、第二阶段已经按本文路径实施：

- 新增 `airport_sim` 正式包，统一提供 `run`、`serve`、`validate-config` 和 `cache` 命令。
- `start_airport_ui.bat`、`python -m airport_ui` 和旧 Seed Explorer BAT 已成为同一服务实现的兼容入口。
- 项目路径集中在 `airport_sim.paths`，不依赖当前工作目录。
- 主调度器与 Seed Explorer 服务已移除大段双份导入分支。
- 缓存清理支持只读盘点、计划、显式确认、固定/取消固定、空间统计和删除失败报告。
- 8776 存在监听时禁止破坏性清理；当前 Viewer release、其来源 Run、staging、固定 Run 和 `saves/` 均受保护。
- Seed Explorer 默认只保留最近 2 个有效缓存；失效指纹缓存可以安全重算。
- 动态测试的新 Run 使用 `seed-cache` artifact profile，不再生成未被动态 API 使用的静态 Viewer 文件。
- 固定 Seed 对照验证中，`full` 与 `seed-cache` 的 94 个 CSV 哈希完全一致；2 年样本文件体积减少 70%。
- 已清理 33 个失效缓存、历史测试输出和未引用发布，共释放 624,906,748 字节。
- 旧 `airport/airport/output/` 已在工作区外压缩备份后删除，工作区不再存在第二套输出根。
- CI 在 Windows/Linux、Python 3.13 上安装可编辑包，并验证统一模块和控制台入口。

界面合并仍未进入本轮，实现范围保持在 `Post_Refactor_UI_Consolidation_Plan.md` 中。

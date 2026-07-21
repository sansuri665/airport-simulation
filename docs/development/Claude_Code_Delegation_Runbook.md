# Claude Code Delegation Runbook

本项目涉及 Claude Code（以下简称 CC）的任务，先阅读本手册。

## 使用定位

Codex 负责：

- 把目标、范围和验收条件传给 CC；
- 启动 CC 并监控进程、会话日志和 Git 状态；
- 确认 CC 没有卡住、达到 Token/turn 上限或异常退出；
- 在任务完成、阻塞或失败时报告状态。

除非用户明确要求，Codex 不重复进行完整代码审查；项目专门的审查流程负责审查。

## Windows 全权限启动

当前 Claude Code 版本需要同时使用以下参数：

```powershell
claude.cmd -p "任务提示" `
  --model glm-5.2-next `
  --allow-dangerously-skip-permissions `
  --dangerously-skip-permissions `
  --permission-mode bypassPermissions `
  --max-turns 50
```

用户级 `settings.json` 可配置：

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

全权限模式只应在用户明确授权、项目有 Git 且任务范围明确时使用。不要使用 `git reset --hard` 或 `git checkout --`，除非用户明确要求。

## 中转站配置

Claude Code 使用 Anthropic Messages 协议时，配置：

```text
ANTHROPIC_BASE_URL=<中转站主机地址>
ANTHROPIC_AUTH_TOKEN=<本机环境变量中的 Key>
ANTHROPIC_MODEL=<中转站实际可用模型名>
```

如果供应商教程展示的 API URL 是 `http://host:port/v1`，Claude Code 的 `ANTHROPIC_BASE_URL` 通常应填写 `http://host:port`，由客户端自动请求 `/v1/messages`。实际使用前先用模型列表和最小 Messages 请求验证协议兼容性。

不要把 API Key 写进仓库、提示词、日志、提交记录或本手册。HTTP 中转地址会明文传输 Key，测试后应更换已暴露的 Key。

## 启动与续跑

始终从目标项目根目录启动：

```powershell
cd "C:\d_e\oiltanker\airport"
claude.cmd --model glm-5.2-next --dangerously-skip-permissions
```

非交互任务使用 `-p`。如果达到 `--max-turns`，使用 `-c -p` 继续最近会话：

```powershell
claude.cmd -c -p "继续完成原任务，先检查上轮状态并从未完成处继续。"
```

## 监控节奏

长任务默认每 5 分钟检查一次：

1. CC 进程是否仍存在且响应；
2. 会话日志是否继续增长；
3. Git 状态或目标文件是否有合理变化；
4. 是否出现权限、网络、Token 或 `max_turns` 错误。

除非发生阻塞、异常退出或任务完成，不需要高频报告中间日志。任务完成时只报告简短结果、测试/运行状态和是否产生提交。

## Token 控制

让 CC 读取代码、修改文件和运行测试，能显著减少 Codex 的上下文消耗；但总 Token 不会消失，CC 仍会为项目上下文和工具调用消耗中转站 Token。

控制方式：

- 使用清晰、边界明确的任务提示；
- 每次只执行一个子目标；
- 设置合理的 `--max-turns`；
- 让 CC 最后返回简短摘要；
- Codex 不转发完整会话日志；
- 失败后优先用 `claude -c -p` 续跑，而不是重新发送全部背景。

参考：

- <https://docs.anthropic.com/en/docs/claude-code/cli-usage>
- <https://docs.anthropic.com/en/docs/claude-code/llm-gateway>

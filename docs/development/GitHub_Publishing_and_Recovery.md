# GitHub 发布与故障恢复

本文说明如何把 Airport 的阶段版本安全发布到 GitHub，以及在 GitHub API 正常但 `git push` 失败时怎样诊断。目标是保持本地提交、远端分支和标签指向同一对象，避免因重复尝试留下错误分支、泄露凭据或误删默认分支。

## 0. 本地小版本与 GitHub 大版本

项目采用两级版本边界：

- **小版本只保存在本地 Git。** 完成一个已经验收的子 Goal 后，在当前开发分支形成独立提交，并建立 `vMMDDa`、`vMMDDb` 一类 annotated tag。小版本不推送分支或标签，主要用于本机回退、差异比较和继续开发。
- **大版本才发布到 GitHub。** 多个相关子 Goal 形成可独立运行的阶段成果，完成完整测试、真实界面验收和版本说明后，再建立正式发布分支与标签并推送远端。

本地小版本的最小流程：

```powershell
git status --short
git diff --check
git add <confirmed-paths>
git commit -m "<type>: <completed sub-goal>"
git tag -a vMMDDa -m "local checkpoint vMMDDa: <scope>"
git status --short
```

规则：

1. 小版本也必须先通过与风险相称的测试，不能把“本地”理解为不需要验收。
2. 每个小版本提交只包含已经确认属于该子 Goal 的文件；不使用提交覆盖未确认改动。
3. 小版本默认不执行 `git push`，本地分支显示 `ahead` 是预期状态。
4. 新提交形成后应保持工作区干净；“清理旧记录”指清理零散暂存状态、已合并临时分支或不再需要的本地标签，不重写已经形成的提交历史。
5. 大版本发布后，只有确认小版本提交已经被正式发布提交包含，才可以删除对应本地小标签；提交本身继续由正式分支历史保存。
6. 需要跨机器备份或协作的内容不应长期只留在本地，应提前升级为 GitHub 阶段版本。

## 1. 发布前检查

先确认工作区范围、GitHub 身份和两种网络通道：

```powershell
git status -sb
git diff --check

gh --version
gh auth status
gh api user --jq '.login'

git remote -v
git ls-remote origin
gh repo view --json nameWithOwner,defaultBranchRef,url
```

这些命令检查的是不同层次：

- `gh auth status` 和 `gh api` 验证 GitHub CLI 的 API 登录；
- `git ls-remote` 验证 Git 使用的 HTTPS 或 SSH 传输；
- Codex 中安装的 GitHub 连接器还有独立授权，GitHub CLI 已登录不代表连接器已经连接。

如果 `gh api` 成功而 `git ls-remote` 报 `Failed to connect to github.com port 443`，通常是 Git 传输通道问题，不是账户权限问题。一次超时已经足以进入备用通道诊断，不要连续重复相同的 push。

提交前还应执行与改动范围相称的本地检查。本项目的完整基线见[测试与安全修改](Testing_and_Safe_Changes.md)。

## 2. 首选发布流程

正常情况下始终使用 Git 本身发布，GitHub API 只负责查询和仓库设置：

```powershell
git switch -c agent/<version-name>
git add <confirmed-paths>
git commit -m "preview: publish <version-name>"
git tag -a <tag-name> -m "<tag-name>"

git push -u origin agent/<version-name>
git push origin <tag-name>
```

只有整个工作区都已经确认属于本次发布时才能使用 `git add -A`。发布后至少验证：

```powershell
git status -sb
git rev-parse HEAD
git rev-parse <tag-name>^{}

gh api repos/<owner>/<repo>/branches/<url-encoded-branch> --jq '.commit.sha'
gh api repos/<owner>/<repo>/git/ref/tags/<tag-name> --jq '.object'
```

分支提交、标签解引用后的提交和本地 `HEAD` 应一致。annotated tag 的 ref 首先指向 tag 对象，因此不能只把 tag 对象 SHA 与提交 SHA 直接比较。

## 3. HTTPS 失败时的判断顺序

### 3.1 先测试 GitHub SSH 443

部分网络允许 `api.github.com` 和 SSH 443，却阻断普通 Git HTTPS。先做只读连通性测试：

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 -T -p 443 git@ssh.github.com
```

- 出现成功认证提示：SSH 通道和账户密钥都可用；
- 出现 `Permission denied (publickey)`：网络通道可用，但当前机器没有已注册的 GitHub SSH 密钥；
- 连接超时：SSH 443 也不可用，应停止发布并检查网络或代理。

已配置账户 SSH 密钥时，可以使用 GitHub 官方 443 地址：

```powershell
git remote set-url --push origin ssh://git@ssh.github.com:443/<owner>/<repo>.git
git push -u origin <branch>
git push origin <tag>
```

如果 fetch 仍希望使用 HTTPS，只修改 `--push` URL；发布完成后根据团队约定保留或恢复原地址。长期最省事的方案是为当前用户配置一次 GitHub 账户 SSH 密钥，而不是每次生成临时密钥。

### 3.2 临时 Deploy Key 只作最后回退

只有在用户已授权发布、SSH 443 可达、账户密钥不可用且 Git HTTPS 确认失败时，才考虑仓库级临时写入 Deploy Key。它必须满足：

1. 密钥只在系统临时目录生成，不进入仓库；
2. 私钥内容不打印、不复制到日志；
3. Deploy Key 只授权目标仓库；
4. push、远端 URL 恢复、Deploy Key 撤销和临时目录清理放在同一个 `try/finally` 流程；
5. 完成后通过 `gh api repos/<owner>/<repo>/keys` 确认临时 Key 已不存在。

如果无法保证清理，宁可停止并让维护者配置正式账户 SSH 密钥。

## 4. 不要用 Git Data API 模拟普通 push

GitHub 的 blob、tree、commit 和 ref API 可以上传文件树，但不适合作为日常 `git push` 的替代品：

- Windows PowerShell 5 把 JSON 直接管道传给 `gh api --input -` 时可能产生编码问题，返回 `Problems parsing JSON`；
- GitHub 创建 commit 时可能规范化时间与时区。即使 tree SHA、作者、父提交和消息看起来相同，commit SHA 仍可能与本地不同；
- 创建 ref 前若没有比较本地和远端 tree/commit SHA，容易形成内容相同但历史分叉的分支；
- 中途停止会留下没有 ref 的 blob、tree 或 commit 对象，虽然 GitHub 最终会回收，但会增加排错成本。

如果不得不调用需要 JSON body 的 GitHub API，Windows PowerShell 应使用无 BOM 的 UTF-8 临时文件：

```powershell
$requestFile = [System.IO.Path]::GetTempFileName()
try {
    $json = $payload | ConvertTo-Json -Depth 20 -Compress
    [System.IO.File]::WriteAllText(
        $requestFile,
        $json,
        [System.Text.UTF8Encoding]::new($false)
    )
    gh api --method POST <endpoint> --input $requestFile
} finally {
    [System.IO.File]::Delete($requestFile)
}
```

若远端 tree SHA 与本地一致、commit SHA 却不一致，应在创建 branch/tag ref 前停止，改用真正的 Git 传输。

## 5. 更换或删除默认分支

删除旧默认分支必须是最后一步。安全顺序是：

1. 新分支和标签已经成功推送；
2. GitHub 上的新分支 SHA 与本地 `HEAD` 一致；
3. CI 已触发，至少确认工作流能够读取新分支；
4. 把仓库默认分支切换到新分支并再次读取确认；
5. 才删除旧远端分支 ref；
6. 本地用 `git merge-base --is-ancestor` 确认旧分支历史仍包含在新分支内，再使用 `git branch -d`，不使用强制删除。

仓库设置和删除命令具有破坏性，只能替换明确变量并在只读检查通过后执行：

```powershell
$repo = '<owner>/<repo>'
$newBranch = '<new-default-branch>'
$oldBranch = '<old-default-branch>'

# 先 PATCH default_branch，再 GET 仓库确认。
gh api --method PATCH "repos/$repo" -f default_branch="$newBranch"
gh api "repos/$repo" --jq '.default_branch'

# 仅在上一条输出精确等于 $newBranch 后执行。
gh api --method DELETE "repos/$repo/git/refs/heads/$oldBranch"
```

删除分支只是删除指针；只有旧提交仍被新分支或标签引用时，才能说历史没有丢失。

## 6. 发布后检查 CI

```powershell
gh run list --repo <owner>/<repo> --branch <branch> --limit 5
gh run watch <run-id> --repo <owner>/<repo> --exit-status --interval 5
```

以工作流的最终 `conclusion` 为准。GitHub Actions 关于运行时弃用的 annotation 可以在 CI 成功时出现，它属于后续维护提示，不等于测试失败。

## 7. 常见错误速查

| 现象 | 通常原因 | 下一步 |
| --- | --- | --- |
| `gh auth status` 成功，`git push` 连接 443 超时 | API 与 Git HTTPS 通道状态不同 | 停止重复 push，测试 SSH 443 |
| SSH 返回 `Permission denied (publickey)` | SSH 网络可达，但密钥未注册 | 配置账户 SSH Key，或经授权使用临时 Deploy Key |
| GitHub 连接器提示未连接 | 连接器授权与 `gh` 登录彼此独立 | 使用已登录的 `gh`，或在应用中连接 GitHub |
| `Problems parsing JSON` | PowerShell 管道编码或 BOM | 使用无 BOM UTF-8 临时请求文件 |
| tree SHA 相同但 commit SHA 不同 | Git Data API 规范化提交元数据 | 不创建 ref，改用 Git HTTPS/SSH push |
| 无法删除旧默认分支 | GitHub 仍把它视为默认分支 | 先切换并读取确认新的默认分支 |
| CI 成功但有 Node 运行时 annotation | Action 依赖的运行时进入弃用期 | 记录为维护项，不把它当成本次失败 |

遵循这个顺序时，大多数发布问题会在创建远端分支之前暴露；真正的删除操作则只会发生在新分支、标签和默认分支都已经验证之后。

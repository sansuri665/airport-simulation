# Web Handoff 联络区

`handoff/` 是本地 Airport 工作区与网页版强模型之间的临时运输层，不是源码、正式文档、发布产物或长期归档目录。

项目规范见 [`docs/development/Web_Model_Handoff.md`](../docs/development/Web_Model_Handoff.md)。

约定目录：

```text
handoff/
  README.md       # 唯一应进入 Git 的文件
  outbox/         # 本地生成、等待上传网页的单 Goal 充足上下文包
  inbox/          # 从网页下载、等待本地审查的返回包或补丁
  work/           # 必要时使用的临时解压目录
```

`outbox/`、`inbox/` 和 `work/` 已被 `.gitignore` 排除。目录按需创建，不放 `.gitkeep`，不在这里复制一套长期源码。

最短工作流：

1. 本地确定一个已经写清范围和验收条件的子 Goal；
2. 把足够完整的源码切片、测试、配置或 Schema、背景说明、正反样例和 `HANDOFF_INSTRUCTIONS.md` 放入 `outbox/` 压缩包；
3. 用户把压缩包上传网页版模型；
4. 网页模型返回同路径修改文件或 unified diff，以及 `CHANGE_REPORT.md`；
5. 返回物先进入 `inbox/`，本地审查后再有选择地应用到真实工作区；
6. 本地运行真实测试和浏览器验收，网页模型的“已完成”不替代本地证据。

“单 Goal”不等于“压缩包越小越好”。当实现依赖较深时，可以提供更大的纯源码包，使外部模型能看到真实导入链、测试辅助代码、配置契约和典型数据形状，并能在包内直接运行目标测试。仍应排除 `output/`、玩家存档、完整 Release、缓存、日志和密钥等生成物或敏感内容。

不要在此目录放入 `.git/`、环境变量、API Key、`output/`、`saves/`、完整 Run、Viewer Release 或无关项目副本。

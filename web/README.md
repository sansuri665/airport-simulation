# Web 界面目录

这里保存 8776 本地服务使用的全部前端页面和静态资源：

```text
web/
  pages/    五个 HTML 页面
  static/   页面共用的 CSS 和 JavaScript
```

物理文件位置不会暴露为 `/web/...`。请通过统一服务访问稳定地址：

- `/`
- `/seed-explorer`
- `/global-gdp`
- `/city-markets`
- `/beijing-forecast`

`/beijing-operations` 是指向 `/city-markets` 的迁移重定向。`/static/...` 由服务安全映射到 `web/static/`；模型和 Viewer 数据继续通过 `/output/...` 读取。

页面路由、服务端职责和兼容入口见 [运行与 Web 架构](../docs/architecture/Runtime_and_Web.md)。

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
- `/beijing-operations`
- `/beijing-forecast`

`/static/...` 由服务安全映射到 `web/static/`；模型和 Viewer 数据继续通过
`/output/...` 读取。移动页面文件时必须保持这些 HTTP 地址不变。

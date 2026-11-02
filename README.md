# i18n 数据分支

本分支由 `.github/workflows/01-translate.yml` 自动维护，**请勿手工修改**。

## 目录约定

- `i18n/<版本>/<语言>.json` —— 按上游 Zed 版本归档的翻译，如 `i18n/v0.228.0/zh-CN.json`
- `i18n/<语言>.json` —— 旧版平铺路径，仅作兜底
- `scan_result.json` —— 上次扫描结果与版本号，供增量提取比对
- `string.json` / `string_context.json` —— 提取出的待译字符串与代码上下文
- `sccache/` —— 构建缓存索引

## 工作方式

01 工作流完成后会自动 commit 到本分支；02 构建工作流从这里读取翻译，注入上游源码后编译。

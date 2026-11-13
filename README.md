# ZedG — Zed 编辑器简体中文版

[![GitHub stars][stars-image]][stars-url]
[![Github Downloads][download-image]][download-url]
[![license][license-image]][license-url]

[Zed 编辑器](https://github.com/zed-industries/zed) 的简体中文版。AI 驱动的全自动翻译与构建流水线：跟随上游版本自动提取待译字符串、AI 翻译、替换源码并重新编译，开箱即用。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=WenYin-Community/ZedG&type=Date)](https://star-history.com/#WenYin-Community/ZedG&Date)

> **Zed 汉化版** | Zed 简体中文版 | Zed 中文版 | Zed Chinese | Zed Simplified Chinese | Zed Localized | Zed i18n | Zed l10n

## 招募共同维护者

ZedG 长期招募共同维护者。项目位于 [WenYin-Community](https://github.com/WenYin-Community) 组织，**加入组织即开放仓库推送权限**，可参与翻译审校、构建流水线与发布维护。

感兴趣请通过 [issue](https://github.com/WenYin-Community/ZedG/issues) 或邮箱 [admin@wenyinos.com](mailto:admin@wenyinos.com) 联系，简单介绍你的经验与可投入方向即可。提交前请先跑测试，流水线改动建议先在分支验证。

## 翻译进度

<!-- STATS:START -->
| 语言 | 版本 | 已译 | 总条目 | 覆盖率 |
|------|------|------|--------|--------|
| zh-CN | v1.28.1 | 31,309 | 98,174 | 31.9% |
| zh-CN | v1.27.0 | 30,991 | 96,912 | 32.0% |
| zh-CN | v1.26.2 | 30,702 | 95,358 | 32.2% |

```
zh-CN  ██████████░░░░░░░░░░░░░░░░░░░░  31.9%
zh-CN  ██████████░░░░░░░░░░░░░░░░░░░░  32.0%
zh-CN  ██████████░░░░░░░░░░░░░░░░░░░░  32.2%
```

禁翻清单：58,255 条（文件级 58,255 + 全局 0）
<!-- STATS:END -->

统计口径：提取出的全部用户可见字符串中，已产生非空译文的占比。部分条目（标识符、源码路径、占位符）本身无需翻译，因此覆盖率不会达到 100%。该区块由 `04-stats` 工作流在每次补翻译后自动更新。

## 下载安装

从 [Releases](https://github.com/WenYin-Community/ZedG/releases/latest) 下载对应平台的预编译包：

| 平台 | 文件 | 安装方式 |
|------|------|---------|
| Windows (x86_64) | `zedg-zh-cn-windows-x86_64-*.zip` | 解压后运行 `ZedG.exe` |
| Windows (x86_64) | `zedg-zh-cn-windows-x86_64-*.msi` | 双击安装 |
| Windows (x86_64) | `zedg-setup-windows-x86_64-*.exe` | 安装向导（NSIS，含"覆盖官方 Zed"可选组件） |
| Windows (ARM64) | `zedg-zh-cn-windows-aarch64-*.zip` | 解压后运行 `ZedG.exe` |
| Windows (ARM64) | `zedg-setup-windows-aarch64-*.exe` | 安装向导（NSIS） |
| Linux (x86_64) | `zedg-zh-cn-linux-x86_64-*.tar.gz` | 解压到 `/usr/local` |
| Linux (x86_64) | `zedg-zh-cn-linux-x86_64-*.deb` | `sudo dpkg -i *.deb` |
| Linux (x86_64) | `zedg-zh-cn-linux-x86_64-*.rpm` | `sudo dnf install *.rpm` |
| Linux (ARM64) | `zedg-zh-cn-linux-aarch64-*.tar.gz` | 解压到 `/usr/local` |
| Linux (ARM64) | `zedg-zh-cn-linux-aarch64-*.deb` | `sudo dpkg -i *.deb` |
| Linux (ARM64) | `zedg-zh-cn-linux-aarch64-*.rpm` | `sudo dnf install *.rpm` |
| macOS (Apple Silicon) | `zedg-zh-cn-macos-aarch64-*.dmg` | DMG 拖入 Applications（[说明](#macos-安装)） |
| 源码补丁 | `zedg-zh-cn-source-*.tar.gz` | 供本地编译使用 |

> 当前构建矩阵：Windows（x86_64 / ARM64）、Linux（x86_64 / ARM64）、macOS（Apple Silicon），共 5 个平台。macOS 仅提供 Apple Silicon 构建，Intel 机型可使用源码补丁自行编译。
>
> Linux 包已捆绑 `libgit2` 运行时（`/usr/lib/zedg`），无需用户自行安装。

### Windows（Scoop）

```powershell
scoop bucket add zedg https://github.com/WenYin-Community/scoop-zedg
scoop install zedg
```

更新：`scoop update zedg`。Manifest 随 Release 自动更新。

### Linux（AUR / COPR）

Arch Linux 与 Fedora/RHEL 用户可通过独立打包仓库安装（[WenYin-Community/zed-globalization](https://github.com/WenYin-Community/zed-globalization) 每日自动同步上游版本，并推送 AUR 与 COPR）：

**AUR（Arch Linux，x86_64 / aarch64）：**

```bash
yay -S zedg      # 或 paru -S zedg
```

**COPR（Fedora / RHEL，x86_64 / aarch64）：**

```bash
sudo dnf copr enable ruojiner/zedg
sudo dnf install zedg
```

> 该仓库仅用于 AUR/COPR 打包推送，其 Release 页面只放打包所需的 `tar.gz` 源文件；其他平台安装包以本仓库 Releases 为准。

### macOS（Homebrew）

```bash
brew tap WenYin-Community/zedg
brew install --cask zedg
```

更新：`brew upgrade --cask zedg`。Cask 随 Release 自动更新（仅 Apple Silicon）。

### macOS 安装

**DMG 手动安装：**

从 Releases 下载 `aarch64` 的 DMG，打开后将 ZedG 拖入 Applications。由于构建未经 Apple 签名，首次打开会提示"应用已损坏"，在终端执行以下命令即可：

```bash
sudo xattr -rd com.apple.quarantine /Applications/ZedG.app
```

### 生态兼容（Linux / macOS，可选）

让 ZedG 接管系统里的 `zed` 命令（生态工具、git difftool、终端识别），并注册应用入口：

```bash
./scripts/zedg-activate.sh            # 激活（创建 ~/.local/bin/zed 链接 + desktop 入口）
./scripts/zedg-activate.sh --status   # 查看状态
./scripts/zedg-activate.sh --revert   # 一键还原
```

## 特性

- **简体中文界面**：当前发布语言为 `zh-CN`，翻译引擎保留多语言能力，后续可按需扩展
- AI 自动扫描识别需翻译的 Rust 源文件
- 正则提取双引号字符串 + 代码上下文收集
- AI 并发翻译，三级降级策略（JSON -> XML CDATA -> 编号格式），流式保活避免长响应断连
- 术语表约束 + 翻译一致性检查
- 源码替换多层保护（过滤 + 语法修正 + 受保护区域跳过），覆盖 raw string、KeyContext/KeyBinding、Rust 路径、占位符顺序
- 禁翻清单自动标记（规则 + AI），减少增量翻译重复请求
- CI 错误短码输出，避免 AI 网关原始错误泄露到公开日志
- JSON <-> Excel 双向转换，支持人工校对
- 跨平台构建（Windows x86_64 / ARM64、Linux x86_64 / ARM64、macOS Apple Silicon），含应用图标；Linux 包捆绑 libgit2 运行时
- 分发渠道：GitHub Releases、Scoop（Windows）、Homebrew（macOS），随 Release 自动更新
- GitHub Actions 全自动流水线：扫描 -> 翻译 -> 构建 -> 发布

## 自动化流水线

```
01-translate (每天 12:00)   扫描上游新版本，提取并翻译字符串
       |
02-build                    5 平台编译 + patch_agent_env 补丁，生成 Release
       |
       └── 发布源仓库（scoop-zedg / homebrew-zedg）每日自动同步最新 Release

03-retry-translate (每天 13:00)  不依赖新版本，单独补翻遗漏条目，不触发构建
04-stats                         统计翻译覆盖率
07-mark-untranslatable (每周)    扫描空值，扩充禁翻清单，减少增量翻译重复请求
```

### 版本判定规则

自动构建只跟随上游 **stable** 版本，pre-release 需要手动触发。

| 情况 | 是否自动构建 | 说明 |
|------|------------|------|
| 上游发布 stable 新版本（如 `v1.27.0`） | ✅ | 次日 12:00 触发 |
| 上游发布 pre-release（如 `v1.27.0-pre.1`） | ❌ | 定时任务不检查 pre-release |
| 上游只推 commit 未发版 | ❌ | 仅识别 release tag |
| 该 stable 版本本地已构建过 | ❌ | 按 Release tag 去重跳过 |
| 每日补翻译（03 工作流） | ❌ | `chain=false`，只更新 i18n 分支 |

去重规则：已发布的版本不会被重复构建。手动重建同一版本时，tag 会自动追加序号（`v1.26.2` → `v1.26.2.1`）。

手动构建其它版本：

```bash
# 最新 pre-release
gh workflow run 01-translate.yml --repo WenYin-Community/ZedG \
  -f release_type=pre-release -f chain=true

# 指定任意版本
gh workflow run 02-build.yml --repo WenYin-Community/ZedG -f version=v1.27.0-pre.1

# 重建已发布版本（tag 自动变为 v1.26.2.1）
gh workflow run 02-build.yml --repo WenYin-Community/ZedG -f version=v1.26.2
```

## 异步补翻译

Zed 源码中约 6.5 万条待译字符串的译文为空。这些空值大部分是**本来就不需要翻译**的内容（标识符如 `future_choice`、源码路径、占位符等），但仍有约 5,300 条是可翻译的英文短语。

`03-retry-translate` 用于在**没有上游新版本**时单独提升翻译覆盖率，与发布流程完全解耦：

| 特点 | 说明 |
|------|------|
| **每日自动** | 北京时间 13:00 自动运行一轮，每次 500 条，无需手动 |
| 不依赖新版本 | 直接对现有版本的 `string.json` 补翻 |
| 不触发构建 | 结果只提交到 `i18n` 分支，不占用编译资源 |
| 可分批执行 | `limit` 控制单次条数，适合限时免费 API |
| 进度累积 | 已翻译的条目不会重复请求 |

```bash
# 每次补 800 条，并发 5
gh workflow run 03-retry-translate.yml --repo WenYin-Community/ZedG \
  -f version=v1.26.2 -f limit=800 -f concurrency=5
```

参数说明：

| 参数 | 默认 | 说明 |
|------|------|------|
| `version` | 空 | 目标版本，留空自动取 `i18n` 分支最新版本目录 |
| `limit` | 500 | 单次最多补翻条数，`0` 表示不限 |
| `concurrency` | 5 | AI 并发数，免费额度紧张时建议 3-5 |
| `chain` | false | 补翻完成后是否触发 02 重新构建发布 |

**默认每日自动运行**：北京时间每天 13:00（`cron: 0 5 * * *`），单次 500 条、并发 5，跑完只提交 `i18n` 分支，不触发构建。配置 AI 密钥后无需任何操作即会生效；如需暂停，注释掉 `.github/workflows/03-retry-translate.yml` 顶部的 `schedule` 段即可，手动触发不受影响。

### 优先级排序

补翻不是按顺序取条目，而是先给候选打分排序，优先把「像 UI 文案」的送审：

| 特征 | 分值 |
|------|------|
| 含空格 | +3 |
| 首字母大写 | +2 |
| 长度 > 8 | +2 |
| 纯 ASCII | +1 |
| 标识符（`^[a-z0-9_.-]+$`） | −5 |
| 纯数字 / 符号 | −5 |
| 路径 / URL | −5 |
| 含转义序列 | −2 |

只排序、不硬性排除——`Open` 这类短词仍会翻译，只是排在短语之后。

实测：40 条混合样本（10 标识符 / 10 短语 / 10 URL / 10 短词）中取前 10 条，全部命中 `Clear patch N` 一类短语，标识符与 URL 零命中。

这样单次额度优先花在真正需要翻译的内容上，避免被标识符和路径耗尽。

### 何时停止补翻

补翻的收益是有限的。出现以下信号时，说明高价值条目已基本扫完，可以停掉：

- 单轮有效翻译持续低于 5%（日志里「本次 N 条仍为空」占绝大多数）
- `rejected.json` 的条目增速明显放缓
- 覆盖率连续多日不再上涨

停止方式：注释掉 `.github/workflows/03-retry-translate.yml` 顶部的 `schedule` 段即可，手动触发不受影响。

停掉之后，上游发新版本时走 01 的增量流程即可——新增字符串会被单独翻译，不会重复扫描旧条目。

> 说明：`--retry-empty` 会把「AI 判定无需翻译」而返回空值的条目也纳入重试，因此存在一定重复尝试成本。系统会把这类条目记入 `<语言>.rejected.json` 并在后续跳过，配合优先级排序可让额度利用率持续提升。

## 本地使用

### 安装工具

```bash
# 基础安装（仅替换功能）
pip install .

# 含 AI 翻译功能
pip install ".[ai]"

# 全部功能
pip install ".[all]"
```

### 分步执行

```bash
# 1. AI 扫描：识别哪些 .rs 文件需要翻译
zedl10n scan --source-root zed

# 2. 提取字符串
zedl10n extract --source-root zed --output string.json

# 3. AI 翻译
zedl10n translate --input string.json --output i18n/zh-CN.json --mode full

# 4. 替换源码
zedl10n replace --input i18n/zh-CN.json --source-root zed
```

### 一键流水线

```bash
zedl10n pipeline --source-root zed --lang zh-CN --mode full
```

### 本地构建

```bash
git clone https://github.com/zed-industries/zed.git
zedl10n replace --input i18n/zh-CN.json --source-root zed
python3 patch_agent_env.py --source-root zed
cd zed && cargo build --release
```

> **`patch_agent_env.py` 补丁说明：** Zed 源码中 `agent_server_store.rs` 会强制将 `ANTHROPIC_API_KEY` 设为空字符串，导致用户系统中已配置的 API Key 被清除；同时 `claude.rs` 的 `connect()` 方法没有像 Codex/Gemini 那样从系统环境变量读取并透传 API Key。该补丁自动修复这两个问题：
> - **补丁 1**：删除 `agent_server_store.rs` 中 `env.insert("ANTHROPIC_API_KEY", "")` 的强制清空行
> - **补丁 2**：在 `claude.rs` 的 `connect()` 中注入环境变量透传逻辑，将 `ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`、Bedrock/Vertex 相关变量及 `AWS_*`、`GOOGLE_CLOUD_*` 前缀变量传递给 Claude Code 进程
>
> 脚本幂等安全：通过 `[ZED_GLOBALIZATION_PATCH]` 标记检测是否已打补丁，重复运行自动跳过。支持 `--dry-run` 仅预览不修改。

## AI 配置

| 环境变量 | CLI 参数 | 说明 | 默认值 |
|----------|----------|------|--------|
| `AI_BASE_URL` | `--base-url` | API 地址 | `https://api.openai.com/v1` |
| `AI_API_KEY` | `--api-key` | API 密钥 | 无（必填） |
| `AI_MODEL` | `--model` | 模型名称 | `gpt-4o-mini` |
| `AI_CONCURRENCY` | `--concurrency` | 并发数 | `5` |

支持任何 OpenAI 兼容 API。优先级：CLI 参数 > 环境变量 > 默认值。

## 项目结构

```
zed-globalization/
├── .github/workflows/
│   ├── 01-translate.yml        # 定时扫描 + AI 翻译
│   └── 02-build.yml            # 多平台编译 + 发布
├── config/
│   └── glossary.yaml       # 翻译术语表
├── i18n/                   # 翻译文件（当前发布 zh-CN）
├── src/zedl10n/
│   ├── cli.py              # CLI 入口（scan/extract/translate/replace/consistency/release-notes 等）
│   ├── scan.py             # AI 扫描识别待翻译文件
│   ├── extract.py          # 正则提取字符串 + 上下文
│   ├── translate.py        # AI 并发翻译（三级降级）
│   ├── replace.py          # 源码替换（多级路径解析 + 三层保护）
│   ├── fix_placeholders.py # 占位符错误修复
│   ├── consistency.py      # 翻译一致性与术语表校验
│   ├── release_notes.py    # Release Notes 获取与翻译
│   ├── convert.py          # JSON <-> Excel 转换
│   └── utils.py            # 共享工具与配置
├── scripts/
│   ├── rebrand.py          # 品牌重命名 zed -> zedg
│   └── patch_file_credentials.py
├── patch_agent_env.py      # 编译前补丁：修复 Agent 环境变量透传
└── pyproject.toml
```

## 替换保护机制

源码替换时通过多层机制保障 Rust 编译安全：

1. **翻译过滤**：跳过纯 ASCII 标点字符串，避免破坏数组语法
2. **受保护区域**：跳过字节字符串（`b""`/`br#""#`）和属性宏（`#[action(...)]`）内的替换
3. **引号转义**：译文中的双引号自动转义为 `\"`
4. **语法修正**：替换后自动将字符串间的中文标点（`、`/`，`/`；`）还原为 ASCII 标点

## 鸣谢

- [Zed](https://github.com/zed-industries/zed)
- [a15355447898a/zed-globalization](https://github.com/a15355447898a/zed-globalization) —— 本项目参考的上游实现
- [deevus/zed-windows-builds](https://github.com/deevus/zed-windows-builds)
- [Nriver/zed-translation](https://github.com/Nriver/zed-translation)

## 许可证

[MIT](LICENSE)

[stars-url]: https://github.com/WenYin-Community/ZedG/stargazers
[stars-image]: https://img.shields.io/github/stars/WenYin-Community/ZedG?style=flat-square&logo=github
[download-url]: https://github.com/WenYin-Community/ZedG/releases/latest
[download-image]: https://img.shields.io/github/downloads/WenYin-Community/ZedG/total?style=flat-square&logo=github
[license-url]: https://github.com/WenYin-Community/ZedG/blob/main/LICENSE
[license-image]: https://img.shields.io/github/license/WenYin-Community/ZedG?style=flat-square

---

<details>
<summary>关键词 / Keywords</summary>

Zed 汉化版, Zed 中文版, Zed 编辑器汉化, Zed 编辑器中文版, Zed 编辑器中文, Zed 中文汉化,
Zed 简体中文, Zed 简体中文版, Zed 本地化, Zed 翻译, Zed 国际化,
Zed Chinese, Zed Simplified Chinese, Zed Localization, Zed Globalization,
Zed i18n, Zed l10n, Zed Translation, Zed Editor Chinese, Zed Editor Localized,
Zed 代替 VSCode, Zed 代替 Cursor, Rust 编辑器中文版, 高性能编辑器汉化

</details>

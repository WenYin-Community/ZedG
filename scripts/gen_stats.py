"""统计 i18n 分支各语言的翻译覆盖率，并回写 README 的 STATS 标记区块。

用法：在仓库根目录执行 `python3 scripts/gen_stats.py`
需要 i18n 目录已存在于工作区（通常由 workflow 从 i18n 分支 checkout）。
"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

README = Path("README.md")
I18N_ROOT = "i18n"
BAR_WIDTH = 30
MARKER = re.compile(r"(<!-- STATS:START -->\n)(.*?)(<!-- STATS:END -->)", re.S)


def scan(root: str = I18N_ROOT) -> list[dict]:
    """扫描 <root>/<版本>/<语言>.json，返回统计数据。"""
    rows: list[dict] = []
    for path in sorted(glob.glob(f"{root}/*/*.json")):
        if path.endswith(".rejected.json"):
            continue
        parts = Path(path).parts
        if len(parts) < 3:
            continue
        version, lang = parts[1], Path(path).stem
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"跳过 {path}: {e}", file=sys.stderr)
            continue
        total = sum(len(v) for v in data.values())
        if not total:
            continue
        filled = sum(1 for v in data.values() for t in v.values() if t.strip())
        rows.append(
            {
                "version": version,
                "lang": lang,
                "filled": filled,
                "total": total,
                "pct": filled / total * 100,
            }
        )
    return rows


DNT_PATH = Path("config/do_not_translate.json")


def count_do_not_translate() -> tuple[int, int]:
    """返回 (文件级条目数, 全局条目数)；文件缺失或损坏时返回 (0, 0)。"""
    if not DNT_PATH.exists():
        return 0, 0
    try:
        data = json.loads(DNT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, 0
    return len(data.get("entries", [])), len(data.get("global_entries", []))


def _version_key(version: str) -> tuple[int, ...]:
    """把 v1.26.2 之类的版本号转成可比较的数字元组。"""
    return tuple(int(x) for x in re.findall(r"\d+", version))


def _render_table(rows: list[dict]) -> list[str]:
    """渲染覆盖率表格行。"""
    lines = [
        "| 语言 | 版本 | 已译 | 总条目 | 覆盖率 |",
        "|------|------|------|--------|--------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['lang']} | {r['version']} | {r['filled']:,} "
            f"| {r['total']:,} | {r['pct']:.1f}% |"
        )
    return lines


def _render_bars(rows: list[dict], width: int) -> list[str]:
    """渲染字符进度条（width 为语言列统一宽度）。"""
    lines = ["```"]
    for r in rows:
        blocks = round(r["pct"] / 100 * BAR_WIDTH)
        bar = "█" * blocks + "░" * (BAR_WIDTH - blocks)
        lines.append(f"{r['lang']:<{width}}  {bar}  {r['pct']:.1f}%")
    lines.append("```")
    return lines


def render(rows: list[dict], dnt_entries: int = 0, dnt_global: int = 0) -> str:
    """全部版本保留；默认显示最近 3 行，其余折叠；附禁翻清单数量。"""
    if not rows:
        return "> 暂无翻译数据。"

    rows = list(rows)
    rows.sort(key=lambda r: r["lang"])
    rows.sort(key=lambda r: _version_key(r["version"]), reverse=True)

    width = max(len(r["lang"]) for r in rows)
    visible, rest = rows[:3], rows[3:]

    body = "\n".join(_render_table(visible) + [""] + _render_bars(visible, width))
    dnt_line = (
        f"禁翻清单：{dnt_entries + dnt_global:,} 条"
        f"（文件级 {dnt_entries:,} + 全局 {dnt_global:,}）"
    )
    if not rest:
        return f"{body}\n\n{dnt_line}"

    rest_body = "\n".join(
        _render_table(rest) + [""] + _render_bars(rest, width)
    )
    return (
        f"{body}\n\n{dnt_line}\n\n"
        "<details>\n"
        f"<summary>展开查看其余 {len(rest)} 行（共 {len(rows)} 行）</summary>\n\n"
        f"{rest_body}\n\n"
        "</details>"
    )


def main() -> int:
    rows = scan()
    if not rows:
        print("未找到翻译数据，保持 README 不变", file=sys.stderr)
        return 1

    dnt_entries, dnt_global = count_do_not_translate()
    body = render(rows, dnt_entries, dnt_global)
    text = README.read_text(encoding="utf-8")
    if not MARKER.search(text):
        print("README 中缺少 STATS 标记", file=sys.stderr)
        return 1

    README.write_text(
        MARKER.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text),
        encoding="utf-8",
    )

    print(f"已更新 {len(rows)} 种语言:")
    for r in rows:
        print(f"  {r['lang']} {r['version']}: {r['filled']:,}/{r['total']:,} = {r['pct']:.1f}%")
    print(f"禁翻清单: {dnt_entries + dnt_global:,} 条（文件级 {dnt_entries:,} + 全局 {dnt_global:,}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

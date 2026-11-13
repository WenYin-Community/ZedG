"""AI 并发翻译，内置智能过滤"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import re
from pathlib import Path

from .batch import split_batch
from .error_codes import report as report_error
from .prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    XML_FALLBACK_INSTRUCTION,
    build_consistency_fix_prompt,
    build_fix_prompt,
    build_numbered_instruction,
    build_user_prompt,
    validate_placeholders,
)
from .utils import (
    AIConfig,
    ProgressBar,
    TranslationDict,
    build_glossary_section,
    check_rust_paths,
    load_json,
    normalize_fullwidth,
    number_anonymous_placeholders,
    parse_json_response,
    parse_numbered_response,
    parse_xml_response,
    placeholder_markers_in_order,
    restore_anonymous_placeholders,
    save_json,
)

log = logging.getLogger(__name__)

# 流式保活间隔：无新 chunk 超过此时长视为连接僵死（代理/负载均衡空闲
# 超时的典型表现——非流式大响应经常在生成期被中间层掐断），主动放弃重试。
STREAM_IDLE_TIMEOUT = 120.0


_PATH_LIKE = re.compile(r"^(https?://|/|[A-Za-z]:\\|\./|\.\./)")
_IDENT_LIKE = re.compile(r"^[a-z0-9_.\-]+$")
_NUMERIC_LIKE = re.compile(r"^[\d\s.,:%+\-*/]+$")


def _translatability_score(text: str) -> int:
    """给待翻字符串打可翻性分数，分数越高越像需要翻译的 UI 文案。

    含空格、首字母大写、长度较大、纯 ASCII 的英文短语得分高；
    标识符、路径、纯数字符号、含转义序列的测试数据得分低。
    仅用于排序，不硬性排除，避免误杀 "Open" 这类短词。
    """
    t = text.strip()
    if not t:
        return -10

    score = 0
    if " " in t:
        score += 3
    if t[0].isupper():
        score += 2
    if len(t) > 8:
        score += 2
    if t.isascii():
        score += 1
    if _IDENT_LIKE.match(t):
        score -= 5
    if _NUMERIC_LIKE.match(t):
        score -= 5
    if _PATH_LIKE.match(t):
        score -= 5
    if "\\n" in t or "\\t" in t or "\\x" in t:
        score -= 2
    return score


def _load_rejected(path: str) -> set[str]:
    """加载已判定无需翻译的条目，读取失败时返回空集合"""
    if not path or not Path(path).exists():
        return set()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set(data.keys())
    except Exception as e:
        log.warning("读取 rejected 文件失败: %s", e)
        return set()


def _save_rejected(path: str, items: set[str]) -> None:
    """保存已判定无需翻译的条目，避免下次重复请求"""
    if not path:
        return
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(sorted(items), ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
    except Exception as e:
        log.warning("写入 rejected 文件失败: %s", e)


def _retry_after_seconds(err: Exception, default: float = 30.0) -> float:
    """从 429 响应头读取 Retry-After，缺失时用默认值，并限制在 1~120 秒"""
    resp = getattr(err, "response", None)
    headers = getattr(resp, "headers", None)
    if headers:
        for key in ("retry-after", "x-ratelimit-reset-requests"):
            raw = headers.get(key)
            if raw:
                try:
                    return min(max(float(raw), 1.0), 120.0)
                except (TypeError, ValueError):
                    continue
    return default


async def _call_ai(
    client: object,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """调用 AI API（流式）：流式保活 + 限流退避 + 配置错误快速失败。

    流式的意义不在总耗时，而在连接活性：chunk 持续到达证明链路存活，
    代理不会因空闲超时掐断长请求；chunk 间隔超过 STREAM_IDLE_TIMEOUT
    视为链路僵死，主动重试。
    """
    import openai

    for attempt in range(5):
        try:
            stream = await client.chat.completions.create(  # type: ignore[attr-defined]
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=65535,
                stream=True,
                extra_body={"thinking": {"type": "disabled"}},
            )
            chunks: list[str] = []
            while True:
                try:
                    raw = await asyncio.wait_for(
                        stream.__anext__(), timeout=STREAM_IDLE_TIMEOUT,
                    )
                except StopAsyncIteration:
                    break
                if getattr(raw, "choices", None):
                    delta = raw.choices[0].delta.content
                    if delta:
                        chunks.append(delta)
            return "".join(chunks).strip()
        except openai.RateLimitError as e:
            # 429：遵循服务端 Retry-After，避免撞在同一个限流窗口里
            wait = _retry_after_seconds(e)
            if attempt < 4:
                log.warning(
                    "触发限流，等待 %.0fs 后重试 (%d/5)", wait, attempt + 1,
                )
                await asyncio.sleep(wait + random.uniform(0, 2))
                continue
            raise
        except (
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.BadRequestError,
            openai.NotFoundError,
        ):
            # 密钥无效、无权限、参数或模型不存在：重试不会成功
            raise
        except Exception as e:
            if attempt < 4:
                delay = (2**attempt) * 3 + random.uniform(0, 2)
                report_error(log, e, f"重试 {attempt + 1}/5，等待 {delay:.1f}s")
                await asyncio.sleep(delay)
                continue
            raise
    return ""


async def _fetch_translation(
    client: object,
    model: str,
    file_path: str,
    strings: dict[str, str],
    file_content: str,
    system_prompt: str,
) -> dict[str, str]:
    """通过 JSON → XML(CDATA) → 编号格式 三级降级获取翻译结果"""
    import openai

    user_prompt = build_user_prompt(file_path, strings, file_content)

    # 第一级: JSON 格式重试 3 次
    for attempt in range(3):
        try:
            raw = await _call_ai(client, model, system_prompt, user_prompt)
            result = parse_json_response(raw)
            if result:
                return result
        except openai.AuthenticationError:
            # 密钥无效，向上抛出由调用方中止整个任务
            raise
        except Exception as e:
            log.warning("翻译失败 %s: %s", file_path, e)
            return {}

    # 第二级: XML(CDATA) 格式重试 3 次
    xml_prompt = user_prompt + XML_FALLBACK_INSTRUCTION
    for attempt in range(3):
        try:
            raw = await _call_ai(client, model, system_prompt, xml_prompt)
            result = parse_xml_response(raw)
            if result:
                return result
            log.debug("XML 解析重试 (%d/3): %s", attempt + 1, file_path)
        except Exception as e:
            log.warning("翻译失败 %s: %s", file_path, e)
            return {}

    # 第三级: 编号格式重试 3 次
    keys = list(strings.keys())
    numbered_prompt = user_prompt + build_numbered_instruction(len(keys))
    for attempt in range(3):
        try:
            raw = await _call_ai(client, model, system_prompt, numbered_prompt)
            result = parse_numbered_response(raw, keys)
            if result:
                return result
            log.debug("编号格式解析重试 (%d/3): %s", attempt + 1, file_path)
        except Exception as e:
            log.warning("翻译失败 %s: %s", file_path, e)
            return {}

    log.warning(
        "[FAILED] JSON+XML+编号 均失败: %s (%d 条)",
        file_path,
        len(strings),
    )
    return {}


async def _translate_batch(
    client: object,
    model: str,
    file_path: str,
    strings: dict[str, str],
    file_content: str,
    system_prompt: str,
) -> dict[str, str]:
    """翻译一批字符串，含占位符与 Rust 路径校验和自动重试"""
    # 匿名占位符编号化：翻译阶段携带序号，防止译文调换 {} 位置导致参数错位
    numbered: dict[str, str] = {}
    placeholder_map: dict[str, tuple[str, list[str]]] = {}
    for original in strings:
        numbered_original, placeholders = number_anonymous_placeholders(original)
        if numbered_original in placeholder_map:
            # 编号化后与其他原文冲突（如 "{}" 与 "{:?}"），该条不编号
            numbered_original, placeholders = original, []
        numbered[numbered_original] = ""
        placeholder_map[numbered_original] = (original, placeholders)

    # 归一化索引：模型有时把换行输出为字面 \n、或改动首尾空白
    def _normalize_key(s: str) -> str:
        return (
            s.replace("\\r", "\r").replace("\\n", "\n").replace("\\t", "\t")
        ).strip()

    normalized_map: dict[str, tuple[str, list[str]]] = {}
    for nkey, entry in placeholder_map.items():
        normalized_map.setdefault(_normalize_key(nkey), entry)

    def restore(raw_result: dict[str, str]) -> dict[str, str]:
        """把编号化译文还原为原文，并执行路径/占位符护栏。"""
        restored: dict[str, str] = {}
        for numbered_original, value in raw_result.items():
            entry = placeholder_map.get(numbered_original)
            if entry is None:
                # 回退：容忍模型输出中换行/空白的差异
                entry = normalized_map.get(_normalize_key(numbered_original))
            if entry is None:
                log.warning(
                    "模型返回未知 key（占位符标记可能被改写），丢弃: %r [%s]",
                    numbered_original, file_path,
                )
                continue
            original, placeholders = entry
            if value and not placeholder_markers_in_order(value, len(placeholders)):
                log.warning(
                    "占位符顺序错误，丢弃译文: %r → %r [%s]",
                    original, value, file_path,
                )
                value = ""
            elif value:
                value = restore_anonymous_placeholders(value, placeholders)
                if not check_rust_paths(original, value):
                    log.warning(
                        "Rust 路径被改写，丢弃译文: %r → %r [%s]",
                        original, value, file_path,
                    )
                    value = ""
            restored[original] = value
        return restored

    result: dict[str, str] = {}
    for attempt in range(2):
        raw_result = await _fetch_translation(
            client, model, file_path, numbered, file_content, system_prompt,
        )
        if not raw_result:
            if attempt == 0:
                log.warning("翻译批次返回空，重试一次: %s", file_path)
                continue
            return {}
        result = restore(raw_result)
        if result:
            break
        if attempt == 0:
            log.warning("本批译文全部被护栏丢弃，重试一次: %s", file_path)

    if not result:
        return {}

    # 占位符校验 + 重试（最多 2 次）
    for retry in range(2):
        errors = validate_placeholders(result)
        if not errors:
            return result
        log.debug(
            "占位符不匹配 %d 条，重试修正 (%d/2): %s",
            len(errors), retry + 1, file_path,
        )
        fix_prompt = build_fix_prompt(errors, result)
        try:
            raw = await _call_ai(client, model, system_prompt, fix_prompt)
            fixed = parse_json_response(raw)
        except Exception as e:
            log.warning("占位符修正请求失败 %s: %s", file_path, e)
            break
        if fixed:
            for key, val in fixed.items():
                if key in result:
                    result[key] = val

    # 最终校验：仍有问题的条目丢弃为空字符串
    final_errors = validate_placeholders(result)
    for original, (src_ph, dst_ph) in final_errors.items():
        log.warning(
            "占位符校验失败，丢弃译文: %r (原文占位符=%s, 译文占位符=%s) [%s]",
            original, src_ph, dst_ph, file_path,
        )
        result[original] = ""

    return result


def _read_source_file(file_path: str, source_root: str) -> str:
    """读取源文件内容，找不到则返回空字符串"""
    if not source_root:
        return ""
    root = Path(source_root)
    candidates = [root / file_path]
    if file_path.startswith("zed/"):
        candidates.append(root / file_path[4:])
    for p in candidates:
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                return ""
    return ""


async def _ai_fix_consistency(
    client: object,
    model: str,
    system_prompt: str,
    result: TranslationDict,
    glossary_path: str,
) -> tuple[TranslationDict, list[str]]:
    """用 AI 修复一致性问题，返回 (修复后结果, 修复日志)"""
    from .consistency import build_issues_for_ai, check_consistency

    issues = check_consistency(result, glossary_path)
    if not issues:
        return result, []

    log.info("一致性检查发现 %d 个问题，调用 AI 修复", len(issues))
    incon, glossary_v, keep_v = build_issues_for_ai(issues, result)
    if not incon and not glossary_v and not keep_v:
        return result, []

    user_prompt = build_consistency_fix_prompt(incon, glossary_v, keep_v)

    fix_log: list[str] = []
    try:
        raw = await _call_ai(client, model, system_prompt, user_prompt)
        fixed = parse_json_response(raw)
    except Exception as e:
        log.warning("AI 一致性修复请求失败: %s", e)
        return result, fix_log

    if not fixed:
        log.warning("AI 一致性修复返回为空")
        return result, fix_log

    # 将 AI 修正结果应用到所有文件
    for original, new_translation in fixed.items():
        if not new_translation:
            continue
        if not check_rust_paths(original, new_translation):
            log.warning(
                "一致性修复改写了 Rust 路径，忽略: %r → %r",
                original, new_translation,
            )
            continue
        if validate_placeholders({original: new_translation}):
            log.warning(
                "一致性修复破坏了占位符，忽略: %r → %r",
                original, new_translation,
            )
            continue
        applied = 0
        for pairs in result.values():
            if original in pairs and pairs[original]:
                if pairs[original] != new_translation:
                    pairs[original] = new_translation
                    applied += 1
        if applied:
            fix_log.append(
                f'AI 修复: "{original}" → "{new_translation}" '
                f"(更新 {applied} 处)",
            )

    return result, fix_log


async def _translate_async(
    all_strings: TranslationDict,
    existing: TranslationDict,
    mode: str,
    lang: str,
    glossary_path: str,
    ai_cfg: AIConfig,
    source_root: str = "",
    retry_empty: bool = False,
    limit: int = 0,
    rejected_path: str = "",
    skip_sets: tuple[set[tuple[str, str]], set[str]] = (set(), set()),
) -> TranslationDict:
    """异步并发翻译：retry_empty 补翻空值，limit 限制条目数，rejected 跳过已判定无需翻译项"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url=ai_cfg.base_url,
        api_key=ai_cfg.api_key,
        max_retries=0,  # 重试与限流退避统一由 _call_ai 控制，避免 SDK 叠加放大请求量
        timeout=120.0,
    )
    semaphore = asyncio.Semaphore(ai_cfg.concurrency)

    glossary_section = build_glossary_section(glossary_path)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        lang=lang,
        glossary_section=glossary_section,
    )

    result: TranslationDict = {fp: dict(v) for fp, v in existing.items()}
    tasks: list[asyncio.Task] = []

    rejected = _load_rejected(rejected_path)
    if rejected:
        log.info("已跳过 %d 条此前判定无需翻译的条目", len(rejected))

    skip_pairs, skip_global = skip_sets

    # 收集全部候选并按可翻性排序，优先把像 UI 文案的条目送审，
    # 避免 limit 被标识符、路径等低价值条目提前耗尽
    candidates: list[tuple[int, str, str]] = []
    for file_path, strings in all_strings.items():
        if file_path not in result:
            result[file_path] = {}
        existing_entries = result[file_path]
        for s in strings:
            # 禁翻清单（untranslatable 自动标记）命中即跳过，避免重复送 AI
            if s in skip_global or (file_path, s) in skip_pairs:
                continue
            cur = existing_entries.get(s)
            if (
                mode == "full"
                or s not in existing_entries
                or (retry_empty and not cur and s not in rejected)
            ):
                candidates.append((_translatability_score(s), file_path, s))

    candidates.sort(key=lambda item: -item[0])
    if limit > 0:
        candidates = candidates[:limit]

    picked = len(candidates)
    picked_keys = [(fp, s) for _, fp, s in candidates]
    if picked:
        log.info(
            "候选 %d 条，优先级最高示例: %s",
            picked, [s for _, _, s in candidates[:3]],
        )

    by_file: dict[str, dict[str, str]] = {}
    for _, file_path, s in candidates:
        by_file.setdefault(file_path, {})[s] = ""

    for file_path, to_translate in by_file.items():
        raw_content = _read_source_file(file_path, source_root)
        batches, file_content = split_batch(
            to_translate, system_prompt, file_path, raw_content,
        )
        for batch in batches:

            async def do_batch(
                fp: str = file_path,
                b: dict = batch,
                fc: str = file_content,
            ) -> tuple[str, dict[str, str]]:
                async with semaphore:
                    return fp, await _translate_batch(
                        client, ai_cfg.model, fp, b, fc, system_prompt,
                    )

            tasks.append(asyncio.create_task(do_batch()))

    if limit > 0 and picked >= limit:
        log.info("已达本次上限 %d 条，剩余条目留待下次补翻", limit)

    total = len(tasks)
    log.info(
        "共 %d 个翻译批次（待翻 %d 条），并发数 %d",
        total, picked, ai_cfg.concurrency,
    )
    pbar = ProgressBar(total, desc="翻译")

    import openai

    fail_count = 0
    auth_aborted = False
    for coro in asyncio.as_completed(tasks):
        try:
            fp, translations = await coro
        except openai.AuthenticationError:
            log.error("AI 密钥无效或已失效，中止剩余批次")
            auth_aborted = True
            for t in tasks:
                t.cancel()
            break
        if translations:
            result.setdefault(fp, {}).update(translations)
        else:
            fail_count += 1
        pbar.update(extra=f"失败 {fail_count}")
    pbar.finish()

    # AI 一致性修复（最多 2 轮）
    for fix_round in range(2):
        result, ai_fix_log = await _ai_fix_consistency(
            client, ai_cfg.model, system_prompt, result, glossary_path,
        )
        for msg in ai_fix_log:
            log.info("一致性修复 (第 %d 轮): %s", fix_round + 1, msg)
        if not ai_fix_log:
            break

    # 本次尝试后仍为空的条目记为「无需翻译」，否则下次会再次命中形成死循环。
    # 认证失败导致的中止不能计入，否则会把本可翻译的条目永久跳过。
    if retry_empty and rejected_path and picked_keys and not auth_aborted:
        still_empty = {
            s for fp, s in picked_keys
            if not (result.get(fp) or {}).get(s)
        }
        if still_empty:
            merged = rejected | still_empty
            _save_rejected(rejected_path, merged)
            log.info(
                "本次 %d 条仍为空，已记为无需翻译，后续跳过（累计 %d 条）",
                len(still_empty), len(merged),
            )

    return result


def translate_all(
    strings_path: str,
    output_path: str,
    context_path: str = "",
    glossary_path: str = "config/glossary.yaml",
    mode: str = "incremental",
    lang: str = "zh-CN",
    ai_cfg: AIConfig | None = None,
    source_root: str = "",
    retry_empty: bool = False,
    limit: int = 0,
    rejected_path: str = "",
    do_not_translate: str = "",
) -> None:
    """同步入口"""
    if ai_cfg is None:
        ai_cfg = AIConfig()
    ai_cfg.validate()

    all_strings: TranslationDict = load_json(strings_path)
    existing = load_json(output_path) if Path(output_path).exists() else {}

    from .untranslatable import load_skip_sets

    skip_sets = load_skip_sets(do_not_translate)
    if skip_sets[0] or skip_sets[1]:
        log.info(
            "已加载禁翻清单: %d 条文件级 + %d 条全局",
            len(skip_sets[0]), len(skip_sets[1]),
        )

    result = asyncio.run(
        _translate_async(
            all_strings, existing, mode, lang,
            glossary_path, ai_cfg, source_root,
            retry_empty, limit, rejected_path, skip_sets,
        )
    )
    # 全角 ASCII 符号统一转半角，避免破坏 Rust 源码语法
    for fp in result:
        for s, t in result[fp].items():
            if t:
                result[fp][s] = normalize_fullwidth(t)

    # 规则兜底：AI 修复后仍有问题的，用规则强制统一
    from .consistency import fix_consistency

    result, fix_log = fix_consistency(result, glossary_path)
    for msg in fix_log:
        log.info("规则兜底修复: %s", msg)

    save_json(result, output_path)
    log.info("翻译结果已保存: %s", output_path)


def run(args: argparse.Namespace) -> None:
    """CLI 入口"""
    ai_cfg = AIConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        concurrency=args.concurrency,
    )
    translate_all(
        args.input,
        args.output,
        args.context,
        args.glossary,
        args.mode,
        args.lang,
        ai_cfg,
        source_root=getattr(args, "source_root", ""),
        retry_empty=getattr(args, "retry_empty", False),
        limit=getattr(args, "limit", 0),
        rejected_path=getattr(args, "rejected_file", ""),
        do_not_translate=getattr(args, "do_not_translate", ""),
    )

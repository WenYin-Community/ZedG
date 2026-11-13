"""护栏回归测试：匿名占位符顺序与 Rust 路径保护"""

import unittest
from unittest import mock

from zedl10n import translate
from zedl10n.replace import (
    _filter_replacements,
    _find_protected_ranges,
    _replace_skip_protected,
)
from zedl10n.utils import (
    check_rust_paths,
    number_anonymous_placeholders,
    placeholder_markers_in_order,
    restore_anonymous_placeholders,
)


class AnonymousPlaceholderTest(unittest.TestCase):
    def test_number_restore_roundtrip(self):
        source = "can't build {} action from input value {}: {}"
        numbered, originals = number_anonymous_placeholders(source)
        self.assertEqual(
            numbered,
            "can't build {__PH0__} action from input value {__PH1__}: {__PH2__}",
        )
        self.assertEqual(originals, ["{}", "{}", "{}"])

        good = "无法构建 {__PH0__} 操作 (输入值 {__PH1__}): {__PH2__}"
        self.assertTrue(placeholder_markers_in_order(good, 3))
        self.assertEqual(
            restore_anonymous_placeholders(good, originals),
            "无法构建 {} 操作 (输入值 {}): {}",
        )

    def test_swapped_markers_rejected(self):
        # 本次事故形态：参数顺序被调换
        bad = "无法从输入值 {__PH1__} 构建 {__PH0__} 操作: {__PH2__}"
        self.assertFalse(placeholder_markers_in_order(bad, 3))

    def test_missing_marker_rejected(self):
        self.assertFalse(placeholder_markers_in_order("缺少 {__PH0__}", 2))

    def test_named_and_escaped_untouched(self):
        source = "value {name:?} and {{literal}} plus {:?}"
        numbered, originals = number_anonymous_placeholders(source)
        self.assertEqual(
            numbered, "value {name:?} and {{literal}} plus {__PH0__}",
        )
        self.assertEqual(originals, ["{:?}"])


class RustPathTest(unittest.TestCase):
    def test_path_must_survive(self):
        source = "Deprecated, use workspace::CloseActiveItem"
        self.assertTrue(
            check_rust_paths(source, "已弃用,请使用 workspace::CloseActiveItem"),
        )
        self.assertFalse(
            check_rust_paths(source, "已弃用,请使用 工作区::CloseActiveItem"),
        )

    def test_plain_text_unaffected(self):
        self.assertTrue(check_rust_paths("plain text", "纯文本"))


class ReplaceGuardTest(unittest.TestCase):
    def test_rewritten_rust_path_is_skipped(self):
        source = "Deprecated, use workspace::CloseActiveItem"
        clean = _filter_replacements(
            {source: "已弃用,请使用 工作区::CloseActiveItem"}, "x.rs",
        )
        self.assertNotIn(source, clean)

    def test_valid_translation_kept(self):
        source = "Deprecated, use workspace::CloseActiveItem"
        clean = _filter_replacements(
            {source: "已弃用,请使用 workspace::CloseActiveItem"}, "x.rs",
        )
        self.assertEqual(clean[source], "已弃用,请使用 workspace::CloseActiveItem")


class TranslateBatchGuardTest(unittest.IsolatedAsyncioTestCase):
    SOURCE = "can't build {} action from input value {}: {}"

    async def _run(self, translated):
        numbered, _ = number_anonymous_placeholders(self.SOURCE)

        async def fake_fetch(client, model, file_path, strings, content, prompt):
            return {numbered: translated}

        with mock.patch.object(translate, "_fetch_translation", fake_fetch):
            return await translate._translate_batch(
                object(), "model", "x.rs", {self.SOURCE: ""}, "", "prompt",
            )

    async def test_swapped_markers_dropped(self):
        result = await self._run(
            "无法从输入值 {__PH1__} 构建 {__PH0__} 操作: {__PH2__}",
        )
        self.assertEqual(result[self.SOURCE], "")

    async def test_ordered_markers_restored(self):
        result = await self._run(
            "无法构建 {__PH0__} 操作 (输入值 {__PH1__}): {__PH2__}",
        )
        self.assertEqual(result[self.SOURCE], "无法构建 {} 操作 (输入值 {}): {}")

    async def test_rewritten_path_dropped(self):
        source = "Deprecated, use workspace::CloseActiveItem"
        numbered, _ = number_anonymous_placeholders(source)

        async def fake_fetch(client, model, file_path, strings, content, prompt):
            return {numbered: "已弃用,请使用 工作区::CloseActiveItem"}

        with mock.patch.object(translate, "_fetch_translation", fake_fetch):
            result = await translate._translate_batch(
                object(), "model", "x.rs", {source: ""}, "", "prompt",
            )
        self.assertEqual(result[source], "")

    async def test_escaped_newline_key_matched(self):
        """模型把换行输出为字面 \\n 时，归一化后仍应匹配原文。"""
        source = "line1\nline2 {}"
        numbered, _ = number_anonymous_placeholders(source)
        escaped = numbered.replace("\n", "\\n")

        async def fake_fetch(client, model, file_path, strings, content, prompt):
            return {escaped: "行1\\n行2 {__PH0__}"}

        with mock.patch.object(translate, "_fetch_translation", fake_fetch):
            result = await translate._translate_batch(
                object(), "model", "x.rs", {source: ""}, "", "prompt",
            )
        self.assertEqual(result[source], "行1\\n行2 {}")


class KeyContextGuardTest(unittest.TestCase):
    """keymap context 键翻译导致快捷键静默失效的回归测试（issue #1）"""

    SOURCE = '''
        let mut context = KeyContext::new_with_defaults();
        context.add("Workspace");
        key_context.add("Pane");
        ctx.add("Onboarding");
        context.set("keyboard_layout", cx.keyboard_layout().name().to_string());
        cx.bind_keys([gpui::KeyBinding::new(
            "ctrl-enter",
            InlineAssist::default(),
            Some("Terminal"),
        )]);
        let title = Label::new("Terminal");
    '''

    def _replace(self, original, new_value):
        protected = _find_protected_ranges(self.SOURCE)
        return _replace_skip_protected(
            self.SOURCE, f'"{original}"', f'"{new_value}"', protected,
        )[0]

    def test_context_add_keys_protected(self):
        for key in ("Workspace", "Pane", "Onboarding"):
            self.assertIn(f'"{key}"', self._replace(key, "已翻译"))

    def test_keybinding_context_protected(self):
        self.assertIn('"Terminal"', self._replace("Terminal", "终端"))

    def test_ui_label_outside_calls_still_replaced(self):
        result = self._replace(
            "Terminal", "终端",
        )
        self.assertIn('Label::new("终端")', result)


if __name__ == "__main__":
    unittest.main()

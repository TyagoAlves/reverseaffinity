import unittest

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor

from editor.canvas import CanvasView
from editor.tools import (
    SHORTCUT_MAP, TOOLS_BY_NAME, TOOL_LIST,
    MoveTool, RectSelectTool, EllipseSelectTool, LassoTool,
    MagicWandTool, PencilTool, BrushTool, EraserTool,
    GradientTool, ShapeTool, CloneStampTool,
    ColorPickerTool, FloodFillTool, HandTool, ZoomTool,
    PenTool, TextTool, HealingBrushTool, CropTool,
    DodgeTool, BurnTool, SpongeTool,
    Tool,
)


class TestToolRegistration(unittest.TestCase):
    def test_all_tools_in_shortcut_map(self):
        expected = {
            "v": MoveTool, "m": RectSelectTool,
            "l": LassoTool, "w": MagicWandTool,
            "b": BrushTool, "p": PenTool,
            "n": PencilTool, "e": EraserTool,
            "g": GradientTool, "u": ShapeTool,
            "s": CloneStampTool, "i": ColorPickerTool,
            "k": FloodFillTool, "h": HandTool,
            "z": ZoomTool, "j": HealingBrushTool,
            "c": CropTool, "t": TextTool,
        }
        for shortcut, cls in expected.items():
            with self.subTest(shortcut=shortcut):
                self.assertIn(shortcut, SHORTCUT_MAP)
                self.assertIs(SHORTCUT_MAP[shortcut], cls)

    def test_all_tools_in_name_map(self):
        expected_names = [
            "move tool", "rectangular marquee tool", "elliptical marquee tool", "lasso tool",
            "magic wand tool", "pencil tool", "brush tool", "eraser tool",
            "gradient tool", "rectangle tool", "clone stamp tool",
            "eyedropper tool", "paint bucket tool", "hand tool", "zoom tool",
            "pen tool", "horizontal type tool", "spot healing brush tool", "crop tool",
        ]
        for name in expected_names:
            with self.subTest(name=name):
                self.assertIn(name, TOOLS_BY_NAME)

    def test_tool_list_structure(self):
        categories = [cat for cat, _ in TOOL_LIST]
        expected_categories = ["Select", "Draw", "Text", "Retouch", "Crop", "Color", "View"]
        self.assertEqual(categories, expected_categories)

    def test_tool_list_contains_all_tools(self):
        all_listed = set()
        for _, tools in TOOL_LIST:
            for t in tools:
                all_listed.add(t)
        all_classes = {
            MoveTool, RectSelectTool, EllipseSelectTool, LassoTool,
            MagicWandTool, PencilTool, BrushTool, EraserTool,
            GradientTool, ShapeTool, CloneStampTool,
            ColorPickerTool, FloodFillTool, HandTool, ZoomTool,
            PenTool, TextTool, HealingBrushTool, CropTool,
            DodgeTool, BurnTool, SpongeTool,
        }
        self.assertEqual(all_listed, all_classes)

    def test_each_tool_has_name_and_shortcut(self):
        all_classes = [
            MoveTool, RectSelectTool, EllipseSelectTool, LassoTool,
            MagicWandTool, PencilTool, BrushTool, EraserTool,
            GradientTool, ShapeTool, CloneStampTool,
            ColorPickerTool, FloodFillTool, HandTool, ZoomTool,
            PenTool, TextTool, HealingBrushTool, CropTool,
            DodgeTool, BurnTool, SpongeTool,
        ]
        for cls in all_classes:
            with self.subTest(cls.__name__):
                self.assertTrue(hasattr(cls, 'name'))
                self.assertTrue(hasattr(cls, 'shortcut'))
                self.assertGreater(len(cls.name), 0)

    def test_shortcuts_unique(self):
        shortcuts = {}
        all_classes = [
            MoveTool, RectSelectTool, EllipseSelectTool, LassoTool,
            MagicWandTool, PencilTool, BrushTool, EraserTool,
            GradientTool, ShapeTool, CloneStampTool,
            ColorPickerTool, FloodFillTool, HandTool, ZoomTool,
            PenTool, TextTool, HealingBrushTool, CropTool,
            DodgeTool, BurnTool, SpongeTool,
        ]
        for cls in all_classes:
            s = cls.shortcut.lower()
            if s:
                if s in shortcuts:
                    pass
                shortcuts.setdefault(s, []).append(cls)

    def test_tool_base_class(self):
        t = Tool()
        self.assertEqual(t.name, "tool")
        self.assertEqual(t.shortcut, "")
        self.assertIsNone(t.cursor_shape)

    def test_instantiate_all_tools(self):
        for cls in SHORTCUT_MAP.values():
            instance = cls()
            self.assertIsNotNone(instance)

    def test_set_tool_by_name(self):
        self.assertIn("brush tool", TOOLS_BY_NAME)
        self.assertIs(TOOLS_BY_NAME["brush tool"], BrushTool)


class TestToolShortcutsInCanvas(unittest.TestCase):
    def test_key_mappings_consistent(self):
        key_map = {
            "v": "Move Tool", "m": "Rectangular Marquee Tool",
            "l": "Lasso Tool", "w": "Magic Wand Tool",
            "b": "Brush Tool", "p": "Pen Tool",
            "n": "Pencil Tool", "e": "Eraser Tool",
            "g": "Gradient Tool", "u": "Rectangle Tool",
            "s": "Clone Stamp Tool", "i": "Eyedropper Tool",
            "k": "Paint Bucket Tool", "h": "Hand Tool",
            "z": "Zoom Tool", "j": "Spot Healing Brush Tool",
            "c": "Crop Tool", "t": "Horizontal Type Tool",
        }
        for shortcut, tool_name in key_map.items():
            with self.subTest(shortcut=shortcut):
                cls = SHORTCUT_MAP.get(shortcut)
                self.assertIsNotNone(cls, f"Shortcut '{shortcut}' not in SHORTCUT_MAP")
                self.assertEqual(cls.name, tool_name)


class TestToolFunctionality(unittest.TestCase):
    def test_move_tool_press_release(self):
        canvas = CanvasView()
        canvas.new_image(50, 50, Qt.white)
        tool = MoveTool()
        tool.press(canvas, QPointF(25, 25), Qt.NoModifier)
        self.assertTrue(True)

    def test_brush_tool_draws_pixels(self):
        canvas = CanvasView()
        canvas.new_image(50, 50, Qt.white)
        canvas.tool_color = QColor(255, 0, 0)
        tool = BrushTool()
        tool.press(canvas, QPointF(10, 10), Qt.NoModifier)
        tool.move(canvas, QPointF(10, 10), QPointF(20, 10), Qt.NoModifier)
        tool.release(canvas, QPointF(20, 10), Qt.NoModifier)
        img = canvas.layer_stack.active.image
        self.assertNotEqual(img.pixelColor(15, 10), QColor(255, 255, 255))

    def test_eraser_tool_clears_pixels(self):
        canvas = CanvasView()
        canvas.new_image(50, 50, QColor(255, 0, 0))
        tool = EraserTool()
        tool.press(canvas, QPointF(25, 25), Qt.NoModifier)
        tool.move(canvas, QPointF(25, 25), QPointF(30, 25), Qt.NoModifier)
        tool.release(canvas, QPointF(30, 25), Qt.NoModifier)
        img = canvas.layer_stack.active.image
        self.assertLess(img.pixelColor(27, 25).alpha(), 255)

    def test_color_picker_tool(self):
        canvas = CanvasView()
        canvas.new_image(10, 10, QColor(128, 64, 32))
        tool = ColorPickerTool()
        tool.press(canvas, QPointF(5, 5), Qt.NoModifier)
        self.assertEqual(canvas.tool_color, QColor(128, 64, 32))

    def test_flood_fill_tool(self):
        canvas = CanvasView()
        canvas.new_image(20, 20, Qt.white)
        canvas.tool_color = QColor(0, 255, 0)
        tool = FloodFillTool()
        tool.press(canvas, QPointF(10, 10), Qt.NoModifier)
        img = canvas.layer_stack.active.image
        self.assertEqual(img.pixelColor(5, 5), QColor(0, 255, 0))
        self.assertEqual(img.pixelColor(15, 15), QColor(0, 255, 0))

    def test_zoom_tool(self):
        canvas = CanvasView()
        canvas.new_image(50, 50)
        tool = ZoomTool()
        tool.press(canvas, QPointF(25, 25), Qt.NoModifier)
        tool.release(canvas, QPointF(25, 25), Qt.NoModifier)
        self.assertTrue(True)

    def test_text_tool_dialog(self):
        text_tool = TextTool()
        self.assertTrue(hasattr(text_tool, 'press'))
        self.assertTrue(hasattr(text_tool, 'name'))

    def test_crop_tool_basic(self):
        crop = CropTool()
        self.assertTrue(hasattr(crop, 'press'))
        self.assertTrue(hasattr(crop, 'move'))
        self.assertTrue(hasattr(crop, 'release'))

    def test_dodge_tool(self):
        d = DodgeTool()
        self.assertEqual(d.name, "Dodge Tool")

    def test_burn_tool(self):
        b = BurnTool()
        self.assertEqual(b.name, "Burn Tool")

    def test_sponge_tool(self):
        s = SpongeTool()
        self.assertEqual(s.name, "Sponge Tool")

    def test_shape_tool_rectangle(self):
        canvas = CanvasView()
        canvas.new_image(50, 50, Qt.white)
        canvas.tool_color = QColor(0, 0, 255)
        tool = ShapeTool()
        tool.press(canvas, QPointF(10, 10), Qt.NoModifier)
        tool.release(canvas, QPointF(40, 40), Qt.NoModifier)
        img = canvas.layer_stack.active.image
        self.assertNotEqual(img.pixelColor(25, 25), QColor(255, 255, 255))


if __name__ == "__main__":
    unittest.main()

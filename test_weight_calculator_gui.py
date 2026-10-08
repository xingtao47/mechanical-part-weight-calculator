import math
import copy
import json
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import weight_calculator
import weight_calculator_gui


class EditableRecordTests(unittest.TestCase):
    def test_saved_parameters_restore_custom_material_and_precise_dimensions(self):
        result = weight_calculator_gui.calculate_part_from_inputs(
            "精密套筒", "3", "空心圆柱", "毫米（mm）",
            {"outer_diameter": "20.1234567890123", "inner_diameter": "10", "length": "40"},
            "自定义材料", "钢", "7.9",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "可编辑清单.mpwc"
            weight_calculator.save_project_file([result["record"]], path)
            loaded = weight_calculator.load_project_file(path)[0]

        self.assertEqual(loaded, result["record"])
        self.assertEqual(loaded["inputs"]["dimensions"]["outer_diameter"], 20.1234567890123)
        self.assertTrue(loaded["inputs"]["custom_material"])
        self.assertEqual(loaded["inputs"]["density_g_per_cm3"], 7.9)

    def test_project_rejects_dimensions_inconsistent_with_weight(self):
        record = weight_calculator_gui.calculate_part_from_inputs(
            "底板", "2", "矩形块", "厘米（cm）",
            {"length": "10", "width": "5", "height": "2"}, "铝",
        )["record"]
        record["inputs"]["dimensions"]["height"] = 4
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "尺寸|重量"):
                weight_calculator.save_project_file([record], Path(directory) / "错误.mpwc")

    def test_overflow_is_reported_as_input_error(self):
        with self.assertRaises(ValueError):
            weight_calculator_gui.calculate_part_from_inputs(
                "超大零件", "1", "实心圆柱", "米（m）",
                {"diameter": "1e200", "length": "1e200"}, "钢",
            )

    def test_old_project_remains_readable_without_inventing_dimensions(self):
        record = weight_calculator.create_part_record("旧轴", "钢", 2, 1.25)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "旧清单.mpwc"
            path.write_text(json.dumps({
                "format": weight_calculator.PROJECT_FILE_FORMAT,
                "format_version": 1, "app_version": "2.1", "records": [record],
            }), encoding="utf-8")
            self.assertEqual(weight_calculator.load_project_file(path), [record])

    def test_malformed_parameters_are_rejected_when_opening(self):
        original = weight_calculator_gui.calculate_part_from_inputs(
            "套筒", "2", "空心圆柱", "毫米（mm）",
            {"outer_diameter": "20", "inner_diameter": "10", "length": "40"}, "钢",
        )["record"]
        mutations = [
            ("dimensions", None), ("part_type", []), ("unit", "inch"),
            ("density_g_per_cm3", True), ("density_g_per_cm3", float("inf")),
            ("custom_material", "false"),
            ("dimensions", {"outer_diameter": 20, "inner_diameter": 30, "length": 40}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "损坏清单.mpwc"
            for key, value in mutations:
                with self.subTest(key=key, value=value):
                    record = copy.deepcopy(original)
                    record["inputs"][key] = value
                    path.write_text(json.dumps({
                        "format": weight_calculator.PROJECT_FILE_FORMAT,
                        "format_version": 2, "records": [record],
                    }), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        weight_calculator.load_project_file(path)


class GuiEditingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as error:
            raise unittest.SkipTest(f"图形环境不可用：{error}")

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.app = weight_calculator_gui.WeightCalculatorApp(self.root)
        self.dialogs = patch.multiple(
            weight_calculator_gui.messagebox,
            showinfo=unittest.mock.DEFAULT, showerror=unittest.mock.DEFAULT,
            askyesno=unittest.mock.DEFAULT, askyesnocancel=unittest.mock.DEFAULT,
        )
        self.mocks = self.dialogs.start()
        self.addCleanup(self.dialogs.stop)

    def add_part(self, name="轴 A", **overrides):
        arguments = dict(
            part_name=name, quantity_text="2", part_type_name="实心圆柱",
            unit_name="毫米（mm）", dimension_values={"diameter": "10", "length": "20"},
            material_choice="钢",
        )
        arguments.update(overrides)
        record = weight_calculator_gui.calculate_part_from_inputs(**arguments)["record"]
        self.app.records.append(record)
        self.app._refresh_records_table()
        return self.app.tree.get_children()[-1]

    def test_edit_updates_one_row_and_summary_without_adding_duplicate(self):
        item = self.add_part()
        self.app._edit_selected(item)
        self.assertEqual(float(self.app.dimension_entries["diameter"].get()), 10)
        original_weight = self.app.records[0]["unit_weight_kg"]
        self.app.part_name_var.set("轴 B")
        self.app.quantity_var.set("3")
        entry = self.app.dimension_entries["diameter"]
        entry.delete(0, "end")
        entry.insert(0, "20")
        self.assertTrue(self.app._calculate_and_add())
        self.assertEqual(len(self.app.records), 1)
        self.assertEqual(self.app.records[0]["name"], "轴 B")
        self.assertAlmostEqual(self.app.records[0]["unit_weight_kg"], original_weight * 4)
        self.assertAlmostEqual(self.app.records[0]["total_weight_kg"], original_weight * 12)
        self.assertIn("总数量：3", self.app.summary_var.get())
        self.assertEqual(self.app.tree.get_children(), (item,))
        self.assertTrue(self.app.has_unsaved_changes)
        self.assertIsNone(self.app.editing_item)

    def test_invalid_edit_preserves_record_and_form(self):
        item = self.add_part()
        before = copy.deepcopy(self.app.records)
        self.app._edit_selected(item)
        self.app.quantity_var.set("0")
        self.assertFalse(self.app._calculate_and_add())
        self.assertEqual(self.app.records, before)
        self.assertEqual(self.app.quantity_var.get(), "0")
        self.assertEqual(self.app.editing_item, item)
        self.assertFalse(self.app.has_unsaved_changes)
        self.mocks["showerror"].assert_called_once()

    def test_cancel_edit_preserves_saved_record(self):
        item = self.add_part()
        before = copy.deepcopy(self.app.records)
        self.app._edit_selected(item)
        self.app.part_name_var.set("放弃的名称")
        self.mocks["askyesno"].return_value = False
        self.app._clear_inputs()
        self.assertEqual(self.app.editing_item, item)
        self.mocks["askyesno"].return_value = True
        self.app._clear_inputs()
        self.assertIsNone(self.app.editing_item)
        self.assertEqual(self.app.records, before)
        self.assertFalse(self.app.has_unsaved_changes)

    def test_delete_other_row_does_not_redirect_edit_to_wrong_record(self):
        self.add_part("轴 A")
        edited = self.add_part("轴 B")
        first = self.app.tree.get_children()[0]
        self.app._edit_selected(edited)
        self.app.part_name_var.set("轴 B 改")
        self.app.tree.selection_set(first)
        self.app._delete_selected()
        self.assertTrue(self.app._calculate_and_add())
        self.assertEqual([r["name"] for r in self.app.records], ["轴 B 改"])

    def test_delete_edited_row_exits_edit_mode(self):
        item = self.add_part()
        self.app._edit_selected(item)
        self.app._delete_selected()
        self.assertEqual(self.app.records, [])
        self.assertIsNone(self.app.editing_item)
        self.assertEqual(self.app.submit_button.cget("text"), "计算并添加")

    def test_edit_saved_custom_material_recovers_exact_inputs(self):
        self.add_part(
            material_choice="自定义材料", custom_material_name="钢", custom_density_text="7.9",
            part_type_name="矩形块", unit_name="厘米（cm）",
            dimension_values={"length": "10.1234567890123", "width": "5", "height": "2"},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "已保存.mpwc"
            weight_calculator.save_project_file(self.app.records, path)
            self.app.records = weight_calculator.load_project_file(path)
        self.app._refresh_records_table()
        self.app._edit_selected(self.app.tree.get_children()[0])
        self.assertEqual(self.app.part_type_var.get(), "矩形块")
        self.assertEqual(self.app.unit_var.get(), "厘米（cm）")
        self.assertEqual(self.app.material_var.get(), "自定义材料")
        self.assertEqual(self.app.custom_material_var.get(), "钢")
        self.assertEqual(self.app.custom_density_var.get(), "7.9")
        self.assertEqual(self.app.dimension_entries["length"].get(), "10.1234567890123")

    def test_legacy_edit_changes_quantity_without_recalculating_geometry(self):
        self.app.records = [weight_calculator.create_part_record("旧轴", "黄铜", 2, 1.25)]
        self.app._refresh_records_table()
        self.app._edit_selected(self.app.tree.get_children()[0])
        self.assertTrue(self.app.legacy_edit)
        self.app.quantity_var.set("4")
        self.app.part_name_var.set("旧轴改")
        self.assertTrue(self.app._calculate_and_add())
        self.assertEqual(self.app.records[0], weight_calculator.create_part_record("旧轴改", "黄铜", 4, 1.25))
        self.assertEqual(self.app.volume_result_var.get(), "未保存尺寸")
        self.assertFalse(self.app.legacy_edit)

    def test_save_applies_pending_edit_before_writing_file(self):
        item = self.add_part()
        self.app._edit_selected(item)
        self.app.quantity_var.set("5")
        self.mocks["askyesnocancel"].return_value = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "更新清单.mpwc"
            self.app.current_project_path = path
            self.app._save_project()
            loaded = weight_calculator.load_project_file(path)
            self.assertEqual(loaded[0]["quantity"], 5)
        self.assertFalse(self.app.has_unsaved_changes)

    def test_cancel_pending_edit_stops_file_save(self):
        item = self.add_part()
        self.app._edit_selected(item)
        self.app.quantity_var.set("5")
        self.mocks["askyesnocancel"].return_value = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "不应保存.mpwc"
            self.app.current_project_path = path
            self.app._save_project()
            self.assertFalse(path.exists())
        self.assertEqual(self.app.records[0]["quantity"], 2)
        self.assertEqual(self.app.editing_item, item)

    def test_switching_records_keeps_draft_when_discard_is_declined(self):
        self.add_part("轴 A")
        self.add_part("轴 B")
        first, second = self.app.tree.get_children()
        self.app._edit_selected(first)
        self.app.quantity_var.set("8")
        self.mocks["askyesno"].return_value = False
        self.app._edit_selected(second)
        self.assertEqual(self.app.editing_item, first)
        self.assertEqual(self.app.quantity_var.get(), "8")

    def test_double_click_opens_clicked_row(self):
        item = self.add_part()
        with patch.object(self.app.tree, "identify_region", return_value="cell"), patch.object(
            self.app.tree, "identify_row", return_value=item
        ):
            self.app._on_double_click(SimpleNamespace(x=40, y=40))
        self.assertEqual(self.app.editing_item, item)

    def test_multi_selection_does_not_choose_a_record_arbitrarily(self):
        self.add_part("轴 A")
        self.add_part("轴 B")
        self.app.tree.selection_set(self.app.tree.get_children())
        self.app._edit_selected()
        self.assertIsNone(self.app.editing_item)
        self.mocks["showinfo"].assert_called_once()

    def test_small_window_can_scroll_to_submit_for_custom_material(self):
        self.root.geometry("980x620+10000+10000")
        self.root.deiconify()
        try:
            self.app.part_type_var.set("矩形块")
            self.app._refresh_dimension_fields()
            self.app.material_var.set("自定义材料")
            self.app._toggle_custom_material_fields()
            self.root.update()
            self.app.input_canvas.yview_moveto(1)
            self.root.update()
            canvas = self.app.input_canvas
            button = self.app.submit_button
            self.assertGreaterEqual(button.winfo_rooty(), canvas.winfo_rooty())
            self.assertLessEqual(
                button.winfo_rooty() + button.winfo_height(),
                canvas.winfo_rooty() + canvas.winfo_height(),
            )
        finally:
            self.root.withdraw()


class GuiInputValidationTests(unittest.TestCase):
    def test_positive_number_accepts_decimal(self):
        self.assertEqual(
            weight_calculator_gui.parse_positive_number("10.5", "直径"),
            10.5,
        )

    def test_positive_number_rejects_text_zero_and_negative(self):
        for value in ("abc", "0", "-2", "nan", "inf"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    weight_calculator_gui.parse_positive_number(value, "直径")

    def test_quantity_requires_a_positive_integer(self):
        for value in ("abc", "0", "-2", "1.5"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    weight_calculator_gui.parse_positive_integer(value)

    def test_part_name_cannot_be_empty(self):
        with self.assertRaisesRegex(ValueError, "零件名称不能为空"):
            weight_calculator_gui.calculate_part_from_inputs(
                "   ",
                "1",
                "实心圆柱",
                "毫米（mm）",
                {"diameter": "10", "length": "20"},
                "钢",
            )


class GuiCalculationTests(unittest.TestCase):
    def test_solid_cylinder_uses_selected_unit_and_material(self):
        result = weight_calculator_gui.calculate_part_from_inputs(
            "轴 A",
            "2",
            "实心圆柱",
            "毫米（mm）",
            {"diameter": "10", "length": "20"},
            "钢",
        )

        self.assertAlmostEqual(result["volume_cm3"], 0.5 * math.pi)
        expected_unit_weight = 0.5 * math.pi * 7.85 / 1000
        self.assertAlmostEqual(
            result["record"]["unit_weight_kg"], expected_unit_weight
        )
        self.assertAlmostEqual(
            result["record"]["total_weight_kg"], expected_unit_weight * 2
        )

    def test_hollow_cylinder_rejects_invalid_inner_diameter(self):
        with self.assertRaisesRegex(ValueError, "内径必须小于外径"):
            weight_calculator_gui.calculate_part_from_inputs(
                "套筒 A",
                "1",
                "空心圆柱",
                "厘米（cm）",
                {
                    "outer_diameter": "10",
                    "inner_diameter": "10",
                    "length": "20",
                },
                "钢",
            )

    def test_rectangular_prism_supports_custom_material(self):
        result = weight_calculator_gui.calculate_part_from_inputs(
            "底板 A",
            "4",
            "矩形块",
            "厘米（cm）",
            {"length": "10", "width": "5", "height": "2"},
            "自定义材料",
            "黄铜",
            "8.5",
        )

        self.assertEqual(result["volume_cm3"], 100)
        self.assertEqual(result["record"]["material_name"], "黄铜")
        self.assertAlmostEqual(result["record"]["unit_weight_kg"], 0.85)
        self.assertAlmostEqual(result["record"]["total_weight_kg"], 3.4)

    def test_custom_material_requires_name_and_density(self):
        base_arguments = (
            "底板 A",
            "1",
            "矩形块",
            "厘米（cm）",
            {"length": "10", "width": "5", "height": "2"},
            "自定义材料",
        )

        with self.assertRaisesRegex(ValueError, "材料名称不能为空"):
            weight_calculator_gui.calculate_part_from_inputs(
                *base_arguments, "", "8.5"
            )

        with self.assertRaisesRegex(ValueError, "材料密度必须大于 0"):
            weight_calculator_gui.calculate_part_from_inputs(
                *base_arguments, "黄铜", "0"
            )


class GuiCsvExportTests(unittest.TestCase):
    def test_export_uses_the_selected_file_path(self):
        records = [
            weight_calculator.create_part_record("轴 A", "钢", 2, 1.25)
        ]

        with tempfile.TemporaryDirectory() as temp_directory:
            selected_path = Path(temp_directory) / "我的零件清单.csv"
            saved_path = weight_calculator.export_records_to_csv_file(
                records, selected_path
            )

            self.assertEqual(saved_path, selected_path.resolve())
            self.assertTrue(selected_path.exists())
            self.assertIn("轴 A", selected_path.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()

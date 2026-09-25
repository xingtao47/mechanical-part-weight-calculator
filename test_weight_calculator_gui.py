import math
import tempfile
import unittest
from pathlib import Path

import weight_calculator
import weight_calculator_gui


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

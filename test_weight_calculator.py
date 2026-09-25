import csv
import json
import math
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import weight_calculator


class VolumeCalculationTests(unittest.TestCase):
    def test_solid_cylinder_volume(self):
        volume = weight_calculator.calculate_solid_cylinder_volume(10, 20)

        self.assertAlmostEqual(volume, 500 * math.pi)

    def test_hollow_cylinder_volume(self):
        volume = weight_calculator.calculate_hollow_cylinder_volume(10, 8, 20)

        self.assertAlmostEqual(volume, 180 * math.pi)

    def test_rectangular_prism_volume(self):
        volume = weight_calculator.calculate_rectangular_prism_volume(10, 5, 2)

        self.assertEqual(volume, 100)


class WeightCalculationTests(unittest.TestCase):
    def test_calculate_weight_in_kilograms(self):
        weight_kg = weight_calculator.calculate_weight(1000, 7.85)

        self.assertEqual(weight_kg, 7.85)

    def test_create_part_record_calculates_batch_weight(self):
        record = weight_calculator.create_part_record(
            "轴套 A", "黄铜", 4, 1.25
        )

        self.assertEqual(
            record,
            {
                "name": "轴套 A",
                "material_name": "黄铜",
                "quantity": 4,
                "unit_weight_kg": 1.25,
                "total_weight_kg": 5.0,
            },
        )

    def test_calculate_summary_totals(self):
        records = [
            weight_calculator.create_part_record("轴套 A", "钢", 4, 1.25),
            weight_calculator.create_part_record("底板 B", "铝", 2, 3.8),
        ]

        total_quantity, total_weight_kg = (
            weight_calculator.calculate_summary_totals(records)
        )

        self.assertEqual(total_quantity, 6)
        self.assertAlmostEqual(total_weight_kg, 12.6)

    @patch("builtins.print")
    def test_summary_prints_material_name(self, mock_print):
        records = [
            weight_calculator.create_part_record("轴套 A", "黄铜", 4, 1.25)
        ]

        weight_calculator.print_summary(records)

        self.assertTrue(
            any("黄铜" in str(call) for call in mock_print.call_args_list)
        )


class MaterialInputTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["1"])
    @patch("builtins.print")
    def test_builtin_material_is_still_available(self, mock_print, mock_input):
        material = weight_calculator.choose_material()

        self.assertEqual(material, ("钢", 7.85))

    @patch("builtins.input", side_effect=["5", "黄铜", "8.5"])
    @patch("builtins.print")
    def test_choose_custom_material(self, mock_print, mock_input):
        material = weight_calculator.choose_material()

        self.assertEqual(material, ("黄铜", 8.5))

    @patch("builtins.input", side_effect=["   ", "黄铜", "abc", "0", "8.5"])
    @patch("builtins.print")
    def test_custom_material_rejects_invalid_name_and_density(
        self, mock_print, mock_input
    ):
        material = weight_calculator.read_custom_material()

        self.assertEqual(material, ("黄铜", 8.5))
        mock_print.assert_any_call(
            "输入错误：材料名称不能为空，请重新输入。"
        )
        mock_print.assert_any_call("输入错误：请输入数字，例如 10 或 10.5。")
        mock_print.assert_any_call("输入错误：数值必须大于 0，请重新输入。")


class PartTypeInputTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["4", "3"])
    @patch("builtins.print")
    def test_rectangular_prism_is_a_valid_part_type(self, mock_print, mock_input):
        part_choice = weight_calculator.choose_part_type()

        self.assertEqual(part_choice, "3")
        self.assertEqual(mock_input.call_count, 2)
        mock_print.assert_any_call("输入错误：请选择 1、2 或 3。")


class InnerDiameterInputTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["10", "12", "8"])
    @patch("builtins.print")
    def test_inner_diameter_must_be_smaller_than_outer_diameter(
        self, mock_print, mock_input
    ):
        inner_diameter = weight_calculator.read_inner_diameter(10)

        self.assertEqual(inner_diameter, 8)
        self.assertEqual(mock_input.call_count, 3)
        mock_print.assert_any_call(
            "输入错误：内径必须小于外径 10，请重新输入。"
        )


class PartInformationInputTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["   ", "轴套 A"])
    @patch("builtins.print")
    def test_part_name_cannot_be_empty(self, mock_print, mock_input):
        part_name = weight_calculator.read_part_name()

        self.assertEqual(part_name, "轴套 A")
        self.assertEqual(mock_input.call_count, 2)
        mock_print.assert_called_with("输入错误：零件名称不能为空，请重新输入。")

    @patch("builtins.input", side_effect=["abc", "0", "-2", "1.5", "4"])
    @patch("builtins.print")
    def test_quantity_must_be_a_positive_integer(self, mock_print, mock_input):
        quantity = weight_calculator.read_positive_integer("请输入零件数量：")

        self.assertEqual(quantity, 4)
        self.assertEqual(mock_input.call_count, 5)
        self.assertEqual(mock_print.call_count, 4)


class CsvExportTests(unittest.TestCase):
    def test_export_records_to_csv(self):
        records = [
            weight_calculator.create_part_record("轴套 A", "钢", 4, 1.25),
            weight_calculator.create_part_record("底板 B", "铝", 2, 3.8),
        ]
        export_time = datetime(2026, 9, 23, 15, 30, 0)

        with tempfile.TemporaryDirectory() as temp_directory:
            file_path = weight_calculator.export_records_to_csv(
                records, temp_directory, export_time
            )

            self.assertEqual(
                file_path.name, "weight_summary_20260923_153000.csv"
            )
            with file_path.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(
            rows[0],
            ["零件名称", "材料", "数量", "单件重量(kg)", "总重量(kg)"],
        )
        self.assertEqual(rows[1], ["轴套 A", "钢", "4", "1.250", "5.000"])
        self.assertEqual(rows[2], ["底板 B", "铝", "2", "3.800", "7.600"])
        self.assertEqual(rows[3], ["合计", "", "6", "", "12.600"])

    @patch("builtins.input", side_effect=["maybe", "Y"])
    @patch("builtins.print")
    def test_read_yes_no_retries_invalid_input(self, mock_print, mock_input):
        answer = weight_calculator.read_yes_no("是否保存：")

        self.assertTrue(answer)
        self.assertEqual(mock_input.call_count, 2)
        mock_print.assert_called_with("输入错误：请输入 y 或 n。")

    @patch("weight_calculator.export_records_to_csv")
    @patch("builtins.input", side_effect=["n"])
    def test_skip_csv_export(self, mock_input, mock_export):
        weight_calculator.offer_csv_export([])

        mock_export.assert_not_called()

    @patch(
        "weight_calculator.export_records_to_csv",
        side_effect=OSError("磁盘空间不足"),
    )
    @patch("builtins.input", side_effect=["y"])
    @patch("builtins.print")
    def test_csv_export_reports_save_error(
        self, mock_print, mock_input, mock_export
    ):
        weight_calculator.offer_csv_export([])

        mock_print.assert_called_with("CSV 文件保存失败：磁盘空间不足")


class ProjectFileTests(unittest.TestCase):
    def test_save_and_load_project_preserves_full_precision(self):
        records = [
            weight_calculator.create_part_record(
                "精密轴 A", "钢", 3, 0.123456789012345
            )
        ]

        with tempfile.TemporaryDirectory() as temp_directory:
            project_path = Path(temp_directory) / "测试清单.mpwc"
            saved_path = weight_calculator.save_project_file(
                records, project_path
            )
            loaded_records = weight_calculator.load_project_file(project_path)

            self.assertEqual(saved_path, project_path.resolve())
            self.assertEqual(loaded_records, records)

    def test_load_project_rejects_unknown_file_format(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            project_path = Path(temp_directory) / "错误格式.mpwc"
            project_path.write_text(
                json.dumps(
                    {
                        "format": "other-program",
                        "format_version": 1,
                        "records": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "不是有效的机械零件清单"):
                weight_calculator.load_project_file(project_path)

    def test_load_project_rejects_invalid_record(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            project_path = Path(temp_directory) / "损坏清单.mpwc"
            project_path.write_text(
                json.dumps(
                    {
                        "format": "mechanical-part-weight-calculator",
                        "format_version": 1,
                        "records": [
                            {
                                "name": "错误零件",
                                "material_name": "钢",
                                "quantity": 0,
                                "unit_weight_kg": 1.0,
                                "total_weight_kg": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "零件记录无效"):
                weight_calculator.load_project_file(project_path)


if __name__ == "__main__":
    unittest.main()

import math
import unittest
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
        record = weight_calculator.create_part_record("轴套 A", 4, 1.25)

        self.assertEqual(
            record,
            {
                "name": "轴套 A",
                "quantity": 4,
                "unit_weight_kg": 1.25,
                "total_weight_kg": 5.0,
            },
        )

    def test_calculate_summary_totals(self):
        records = [
            weight_calculator.create_part_record("轴套 A", 4, 1.25),
            weight_calculator.create_part_record("底板 B", 2, 3.8),
        ]

        total_quantity, total_weight_kg = (
            weight_calculator.calculate_summary_totals(records)
        )

        self.assertEqual(total_quantity, 6)
        self.assertAlmostEqual(total_weight_kg, 12.6)


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


if __name__ == "__main__":
    unittest.main()

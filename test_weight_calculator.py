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


if __name__ == "__main__":
    unittest.main()

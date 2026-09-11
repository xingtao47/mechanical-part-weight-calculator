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

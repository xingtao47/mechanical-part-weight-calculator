import math


VERSION = "1.1"
MATERIALS = {
    "1": ("钢", 7.85),
    "2": ("铝", 2.70),
    "3": ("铜", 8.96),
    "4": ("钛", 4.51),
}


def read_positive_number(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            print("输入错误：数值必须大于 0，请重新输入。")
        except ValueError:
            print("输入错误：请输入数字，例如 10 或 10.5。")
def choose_unit():
    print("\n请选择尺寸单位：")
    print("1. 毫米（mm）")
    print("2. 厘米（cm）")
    print("3. 米（m）")

    while True:
        unit_choice = input("请输入选项 1/2/3：").strip()

        if unit_choice == "1":
            return "毫米", 0.1
        if unit_choice == "2":
            return "厘米", 1
        if unit_choice == "3":
            return "米", 100

        print("输入错误：请选择 1、2 或 3。")


def choose_material():
    print("\n请选择材料：")
    for option, (material_name, _) in MATERIALS.items():
        print(f"{option}. {material_name}")

    while True:
        material_choice = input("请输入选项 1/2/3/4：").strip()

        if material_choice in MATERIALS:
            return MATERIALS[material_choice]

        print("输入错误：请选择 1、2、3 或 4。")


def calculate_once():
    print("=" * 40)
    print(f"机械零件重量计算器 V{VERSION}")
    print("=" * 40)
    unit_name, conversion_factor = choose_unit()
    diameter = read_positive_number("请输入圆柱直径：")
    length = read_positive_number("请输入圆柱长度：")

    print("直径：", diameter, unit_name)
    print("长度：", length, unit_name)
    material_name, density = choose_material()

    print("材料：", material_name)
    print("密度：", density, "g/cm^3")

    diameter_cm = diameter * conversion_factor
    length_cm = length * conversion_factor

    print("换算后的直径：", diameter_cm, "cm")
    print("换算后的长度：", length_cm, "cm")
    radius_cm = diameter_cm / 2
    volume_cm3 = math.pi * radius_cm ** 2 * length_cm

    weight_g = volume_cm3 * density
    weight_kg = weight_g / 1000

    print("\n计算结果：")
    print("体积：", round(volume_cm3, 2), "cm^3")
    print("重量：", round(weight_g, 2), "g")
    print("重量：", round(weight_kg, 3), "kg")
while True:
    calculate_once()

    while True:
        again = input("\n是否继续计算？输入 y 继续，输入 n 结束：").strip().lower()

        if again in ("y", "n"):
            break

        print("输入错误：请输入 y 或 n。")

    if again == "n":
        print("程序已结束。")
        break

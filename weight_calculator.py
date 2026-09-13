import math


VERSION = "1.3"
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


def read_inner_diameter(outer_diameter):
    while True:
        inner_diameter = read_positive_number("请输入圆柱内径：")

        if inner_diameter < outer_diameter:
            return inner_diameter

        print(
            f"输入错误：内径必须小于外径 {outer_diameter:g}，请重新输入。"
        )


def choose_part_type():
    print("\n请选择零件类型：")
    print("1. 实心圆柱")
    print("2. 空心圆柱")
    print("3. 矩形块")

    while True:
        part_choice = input("请输入选项 1/2/3：").strip()

        if part_choice in ("1", "2", "3"):
            return part_choice

        print("输入错误：请选择 1、2 或 3。")


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


def calculate_solid_cylinder_volume(diameter_cm, length_cm):
    radius_cm = diameter_cm / 2
    return math.pi * radius_cm ** 2 * length_cm


def calculate_hollow_cylinder_volume(
    outer_diameter_cm, inner_diameter_cm, length_cm
):
    outer_radius_cm = outer_diameter_cm / 2
    inner_radius_cm = inner_diameter_cm / 2
    return math.pi * (outer_radius_cm ** 2 - inner_radius_cm ** 2) * length_cm


def calculate_rectangular_prism_volume(length_cm, width_cm, height_cm):
    return length_cm * width_cm * height_cm


def calculate_once():
    print("=" * 40)
    print(f"机械零件重量计算器 V{VERSION}")
    print("=" * 40)
    part_choice = choose_part_type()
    unit_name, conversion_factor = choose_unit()

    if part_choice == "1":
        diameter = read_positive_number("请输入圆柱直径：")
        length = read_positive_number("请输入圆柱长度：")
        print("直径：", diameter, unit_name)
        print("长度：", length, unit_name)
    elif part_choice == "2":
        outer_diameter = read_positive_number("请输入圆柱外径：")
        inner_diameter = read_inner_diameter(outer_diameter)
        length = read_positive_number("请输入圆柱长度：")
        print("外径：", outer_diameter, unit_name)
        print("内径：", inner_diameter, unit_name)
        print("长度：", length, unit_name)
    else:
        length = read_positive_number("请输入矩形块长度：")
        width = read_positive_number("请输入矩形块宽度：")
        height = read_positive_number("请输入矩形块高度：")
        print("长度：", length, unit_name)
        print("宽度：", width, unit_name)
        print("高度：", height, unit_name)

    material_name, density = choose_material()

    print("材料：", material_name)
    print("密度：", density, "g/cm^3")

    length_cm = length * conversion_factor

    if part_choice == "1":
        diameter_cm = diameter * conversion_factor
        print("换算后的直径：", diameter_cm, "cm")
        print("换算后的长度：", length_cm, "cm")
        volume_cm3 = calculate_solid_cylinder_volume(diameter_cm, length_cm)
    elif part_choice == "2":
        outer_diameter_cm = outer_diameter * conversion_factor
        inner_diameter_cm = inner_diameter * conversion_factor
        print("换算后的外径：", outer_diameter_cm, "cm")
        print("换算后的内径：", inner_diameter_cm, "cm")
        print("换算后的长度：", length_cm, "cm")
        volume_cm3 = calculate_hollow_cylinder_volume(
            outer_diameter_cm, inner_diameter_cm, length_cm
        )
    else:
        width_cm = width * conversion_factor
        height_cm = height * conversion_factor
        print("换算后的长度：", length_cm, "cm")
        print("换算后的宽度：", width_cm, "cm")
        print("换算后的高度：", height_cm, "cm")
        volume_cm3 = calculate_rectangular_prism_volume(
            length_cm, width_cm, height_cm
        )

    weight_g = volume_cm3 * density
    weight_kg = weight_g / 1000

    print("\n计算结果：")
    print("体积：", round(volume_cm3, 2), "cm^3")
    print("重量：", round(weight_g, 2), "g")
    print("重量：", round(weight_kg, 3), "kg")


def main():
    while True:
        calculate_once()

        while True:
            again = input(
                "\n是否继续计算？输入 y 继续，输入 n 结束："
            ).strip().lower()

            if again in ("y", "n"):
                break

            print("输入错误：请输入 y 或 n。")

        if again == "n":
            print("程序已结束。")
            break


if __name__ == "__main__":
    main()

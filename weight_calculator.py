import csv
import json
import math
from datetime import datetime
from pathlib import Path


VERSION = "2.2"
PROJECT_FILE_FORMAT = "mechanical-part-weight-calculator"
PROJECT_FORMAT_VERSION = 2
PART_DIMENSION_KEYS = {
    "solid_cylinder": ("diameter", "length"),
    "hollow_cylinder": ("outer_diameter", "inner_diameter", "length"),
    "rectangular_prism": ("length", "width", "height"),
}
UNIT_FACTORS = {"mm": 0.1, "cm": 1, "m": 100}
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


def read_part_name():
    while True:
        part_name = input("请输入零件名称：").strip()

        if part_name:
            return part_name

        print("输入错误：零件名称不能为空，请重新输入。")


def read_positive_integer(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("输入错误：数量必须是正整数，请重新输入。")
        except ValueError:
            print("输入错误：数量必须是正整数，请重新输入。")


def read_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()

        if answer == "y":
            return True
        if answer == "n":
            return False

        print("输入错误：请输入 y 或 n。")


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


def read_custom_material():
    while True:
        material_name = input("请输入自定义材料名称：").strip()

        if material_name:
            break

        print("输入错误：材料名称不能为空，请重新输入。")

    density = read_positive_number("请输入材料密度（g/cm^3）：")
    return material_name, density


def choose_material():
    print("\n请选择材料：")
    for option, (material_name, _) in MATERIALS.items():
        print(f"{option}. {material_name}")
    print("5. 自定义材料")

    while True:
        material_choice = input("请输入选项 1/2/3/4/5：").strip()

        if material_choice in MATERIALS:
            return MATERIALS[material_choice]
        if material_choice == "5":
            return read_custom_material()

        print("输入错误：请选择 1、2、3、4 或 5。")


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


def calculate_weight(volume_cm3, density_g_per_cm3):
    return volume_cm3 * density_g_per_cm3 / 1000


def _positive_finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}必须是大于 0 的有限数字。")
    try:
        number = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError(f"{label}数值过大。") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label}必须是大于 0 的有限数字。")
    return number


def calculate_volume_from_parameters(part_type, unit, dimensions):
    if not isinstance(part_type, str) or part_type not in PART_DIMENSION_KEYS:
        raise ValueError("零件类型无效。")
    if not isinstance(unit, str) or unit not in UNIT_FACTORS:
        raise ValueError("尺寸单位无效。")
    if not isinstance(dimensions, dict):
        raise ValueError("尺寸数据无效。")
    converted = {
        key: _positive_finite_number(dimensions.get(key), "尺寸") * UNIT_FACTORS[unit]
        for key in PART_DIMENSION_KEYS[part_type]
    }
    try:
        if part_type == "solid_cylinder":
            volume = calculate_solid_cylinder_volume(converted["diameter"], converted["length"])
        elif part_type == "hollow_cylinder":
            if converted["inner_diameter"] >= converted["outer_diameter"]:
                raise ValueError("内径必须小于外径。")
            volume = calculate_hollow_cylinder_volume(
                converted["outer_diameter"], converted["inner_diameter"], converted["length"]
            )
        else:
            volume = calculate_rectangular_prism_volume(
                converted["length"], converted["width"], converted["height"]
            )
    except OverflowError as error:
        raise ValueError("尺寸数值过大，请检查输入。") from error
    return _positive_finite_number(volume, "计算体积")


def _validate_project_inputs(inputs, record, index):
    if not isinstance(inputs, dict):
        raise ValueError(f"第 {index} 条零件记录无效：计算参数损坏。")
    part_type = inputs.get("part_type")
    unit = inputs.get("unit")
    dimensions = inputs.get("dimensions")
    volume = calculate_volume_from_parameters(part_type, unit, dimensions)
    density = _positive_finite_number(inputs.get("density_g_per_cm3"), "材料密度")
    custom_material = inputs.get("custom_material")
    if not isinstance(custom_material, bool):
        raise ValueError(f"第 {index} 条零件记录无效：材料类型损坏。")
    if not custom_material:
        builtin_density = dict(MATERIALS.values()).get(record["material_name"])
        if builtin_density != density:
            raise ValueError(f"第 {index} 条零件记录无效：内置材料和密度不匹配。")
    expected_weight = _positive_finite_number(calculate_weight(volume, density), "计算重量")
    if not math.isclose(record["unit_weight_kg"], expected_weight, rel_tol=1e-12, abs_tol=0):
        raise ValueError(f"第 {index} 条零件记录无效：尺寸、密度与重量不匹配。")
    return {
        "part_type": part_type,
        "unit": unit,
        "dimensions": {key: float(dimensions[key]) for key in PART_DIMENSION_KEYS[part_type]},
        "density_g_per_cm3": density,
        "custom_material": custom_material,
    }


def create_part_record(name, material_name, quantity, unit_weight_kg):
    return {
        "name": name,
        "material_name": material_name,
        "quantity": quantity,
        "unit_weight_kg": unit_weight_kg,
        "total_weight_kg": unit_weight_kg * quantity,
    }


def calculate_summary_totals(records):
    total_quantity = sum(record["quantity"] for record in records)
    total_weight_kg = sum(record["total_weight_kg"] for record in records)
    return total_quantity, total_weight_kg


def _validate_project_record(record, index):
    if not isinstance(record, dict):
        raise ValueError(f"第 {index} 条零件记录无效。")

    name = record.get("name")
    material_name = record.get("material_name")
    quantity = record.get("quantity")
    unit_weight_kg = record.get("unit_weight_kg")
    total_weight_kg = record.get("total_weight_kg")

    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"第 {index} 条零件记录无效：零件名称为空。")
    if not isinstance(material_name, str) or not material_name.strip():
        raise ValueError(f"第 {index} 条零件记录无效：材料名称为空。")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"第 {index} 条零件记录无效：数量必须是正整数。")

    unit_weight_kg = _positive_finite_number(unit_weight_kg, f"第 {index} 条零件单件重量")
    total_weight_kg = _positive_finite_number(total_weight_kg, f"第 {index} 条零件总重量")
    try:
        expected_total = unit_weight_kg * quantity
    except OverflowError as error:
        raise ValueError(f"第 {index} 条零件记录无效：数量过大。") from error
    if not math.isclose(
        total_weight_kg, expected_total, rel_tol=1e-12, abs_tol=1e-12
    ):
        raise ValueError(f"第 {index} 条零件记录无效：总重量不匹配。")

    validated = {
        "name": name.strip(),
        "material_name": material_name.strip(),
        "quantity": quantity,
        "unit_weight_kg": float(unit_weight_kg),
        "total_weight_kg": float(total_weight_kg),
    }
    if "inputs" in record:
        validated["inputs"] = _validate_project_inputs(record["inputs"], validated, index)
    return validated


def save_project_file(records, file_path):
    file_path = Path(file_path)
    validated_records = [
        _validate_project_record(record, index)
        for index, record in enumerate(records, start=1)
    ]
    project_data = {
        "format": PROJECT_FILE_FORMAT,
        "format_version": PROJECT_FORMAT_VERSION,
        "app_version": VERSION,
        "records": validated_records,
    }

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as project_file:
        json.dump(project_data, project_file, ensure_ascii=False, indent=2)

    return file_path.resolve()


def load_project_file(file_path):
    file_path = Path(file_path)
    try:
        with file_path.open(encoding="utf-8") as project_file:
            project_data = json.load(project_file)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("清单文件内容损坏，无法打开。") from error

    if (
        not isinstance(project_data, dict)
        or project_data.get("format") != PROJECT_FILE_FORMAT
    ):
        raise ValueError("这不是有效的机械零件清单文件。")

    format_version = project_data.get("format_version")
    if type(format_version) is not int or format_version not in (1, PROJECT_FORMAT_VERSION):
        raise ValueError("清单文件版本不受支持。")

    records = project_data.get("records")
    if not isinstance(records, list):
        raise ValueError("清单文件内容损坏：缺少零件记录。")

    return [
        _validate_project_record(record, index)
        for index, record in enumerate(records, start=1)
    ]


def export_records_to_csv_file(records, file_path):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    total_quantity, total_weight_kg = calculate_summary_totals(records)

    with file_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["零件名称", "材料", "数量", "单件重量(kg)", "总重量(kg)"]
        )

        for record in records:
            writer.writerow(
                [
                    record["name"],
                    record["material_name"],
                    record["quantity"],
                    f"{record['unit_weight_kg']:.3f}",
                    f"{record['total_weight_kg']:.3f}",
                ]
            )

        writer.writerow(
            ["合计", "", total_quantity, "", f"{total_weight_kg:.3f}"]
        )

    return file_path.resolve()


def export_records_to_csv(
    records, export_directory="exports", export_time=None
):
    export_directory = Path(export_directory)

    if export_time is None:
        export_time = datetime.now()

    timestamp = export_time.strftime("%Y%m%d_%H%M%S")
    file_path = export_directory / f"weight_summary_{timestamp}.csv"
    return export_records_to_csv_file(records, file_path)


def offer_csv_export(records):
    should_export = read_yes_no(
        "\n是否将零件清单保存为 CSV 文件？输入 y 保存，输入 n 跳过："
    )

    if not should_export:
        return None

    try:
        file_path = export_records_to_csv(records)
    except OSError as error:
        print(f"CSV 文件保存失败：{error}")
        return None

    print(f"CSV 文件已保存：{file_path}")
    return file_path


def print_summary(records):
    total_quantity, total_weight_kg = calculate_summary_totals(records)

    print("\n零件汇总：")
    print(
        f"{'零件名称':<14}{'材料':<10}{'数量':>6}"
        f"{'单件重量':>16}{'小计':>16}"
    )
    print("-" * 66)

    for record in records:
        print(
            f"{record['name']:<14}"
            f"{record['material_name']:<10}"
            f"{record['quantity']:>6}"
            f"{record['unit_weight_kg']:>13.3f} kg"
            f"{record['total_weight_kg']:>13.3f} kg"
        )

    print("-" * 66)
    print(f"总数量：{total_quantity}")
    print(f"总重量：{total_weight_kg:.3f} kg")


def calculate_once():
    print("=" * 40)
    print(f"机械零件重量计算器 V{VERSION}")
    print("=" * 40)
    part_name = read_part_name()
    quantity = read_positive_integer("请输入零件数量：")
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

    weight_kg = calculate_weight(volume_cm3, density)
    weight_g = weight_kg * 1000
    record = create_part_record(part_name, material_name, quantity, weight_kg)

    print("\n计算结果：")
    print("零件名称：", part_name)
    print("数量：", quantity)
    print("体积：", round(volume_cm3, 2), "cm^3")
    print("重量：", round(weight_g, 2), "g")
    print("重量：", round(weight_kg, 3), "kg")
    print("该批次总重量：", round(record["total_weight_kg"], 3), "kg")

    return record


def main():
    records = []

    while True:
        record = calculate_once()
        records.append(record)

        should_continue = read_yes_no(
            "\n是否继续计算？输入 y 继续，输入 n 结束："
        )

        if not should_continue:
            print_summary(records)
            offer_csv_export(records)
            print("程序已结束。")
            break


if __name__ == "__main__":
    main()

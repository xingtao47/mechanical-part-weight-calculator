import math
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import weight_calculator


PART_TYPES = {
    "实心圆柱": "solid_cylinder",
    "空心圆柱": "hollow_cylinder",
    "矩形块": "rectangular_prism",
}

UNITS = {
    "毫米（mm）": 0.1,
    "厘米（cm）": 1,
    "米（m）": 100,
}
UNIT_CODES = {"毫米（mm）": "mm", "厘米（cm）": "cm", "米（m）": "m"}

MATERIALS_BY_NAME = {
    material_name: density
    for material_name, density in weight_calculator.MATERIALS.values()
}

CUSTOM_MATERIAL = "自定义材料"

DIMENSION_FIELDS = {
    "实心圆柱": (("diameter", "直径"), ("length", "长度")),
    "空心圆柱": (
        ("outer_diameter", "外径"),
        ("inner_diameter", "内径"),
        ("length", "长度"),
    ),
    "矩形块": (
        ("length", "长度"),
        ("width", "宽度"),
        ("height", "高度"),
    ),
}


def parse_positive_number(value, field_name):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name}必须是数字。") from error

    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field_name}必须大于 0。")

    return number


def parse_positive_integer(value, field_name="数量"):
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name}必须是正整数。") from error

    if number <= 0:
        raise ValueError(f"{field_name}必须是正整数。")

    return number


def calculate_part_from_inputs(
    part_name,
    quantity_text,
    part_type_name,
    unit_name,
    dimension_values,
    material_choice,
    custom_material_name="",
    custom_density_text="",
):
    part_name = part_name.strip()
    if not part_name:
        raise ValueError("零件名称不能为空。")

    quantity = parse_positive_integer(quantity_text)

    if part_type_name not in PART_TYPES:
        raise ValueError("请选择有效的零件类型。")

    if unit_name not in UNITS:
        raise ValueError("请选择有效的尺寸单位。")

    dimensions = {}
    for field_key, field_label in DIMENSION_FIELDS[part_type_name]:
        dimensions[field_key] = parse_positive_number(
            dimension_values.get(field_key, ""), field_label
        )

    if material_choice == CUSTOM_MATERIAL:
        material_name = custom_material_name.strip()
        if not material_name:
            raise ValueError("自定义材料名称不能为空。")
        density = parse_positive_number(custom_density_text, "材料密度")
    elif material_choice in MATERIALS_BY_NAME:
        material_name = material_choice
        density = MATERIALS_BY_NAME[material_choice]
    else:
        raise ValueError("请选择有效的材料。")

    # Preserve dimensions in the entered unit, without rounding or converting back.
    volume_cm3 = weight_calculator.calculate_volume_from_parameters(
        PART_TYPES[part_type_name], UNIT_CODES[unit_name], dimensions
    )
    try:
        unit_weight_kg = weight_calculator.calculate_weight(volume_cm3, density)
        record = weight_calculator.create_part_record(
            part_name, material_name, quantity, unit_weight_kg
        )
    except OverflowError as error:
        raise ValueError("计算结果过大，请检查尺寸、密度和数量。") from error
    record["inputs"] = {
        "part_type": PART_TYPES[part_type_name],
        "unit": UNIT_CODES[unit_name],
        "dimensions": dimensions,
        "density_g_per_cm3": density,
        "custom_material": material_choice == CUSTOM_MATERIAL,
    }
    record = weight_calculator._validate_project_record(record, 1)
    return {
        "record": record,
        "volume_cm3": volume_cm3,
        "weight_g": unit_weight_kg * 1000,
    }


class WeightCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.records = []
        self.dimension_entries = {}
        self.current_project_path = None
        self.has_unsaved_changes = False
        self.editing_item = None
        self.edit_baseline = None
        self.legacy_edit = False

        self._configure_window()
        self._create_variables()
        self._create_widgets()
        self._refresh_dimension_fields()
        self._toggle_custom_material_fields()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_window(self):
        self.root.title(
            f"机械零件重量计算器 V{weight_calculator.VERSION}"
        )
        self.root.geometry("1120x680")
        self.root.minsize(980, 620)
        self.root.option_add("*Font", ("Microsoft YaHei UI", 10))

        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Header.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("ResultTitle.TLabel", foreground="#315f8c")
        style.configure("ResultValue.TLabel", font=("Microsoft YaHei UI", 13, "bold"))
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _create_variables(self):
        self.part_name_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.part_type_var = tk.StringVar(value="实心圆柱")
        self.unit_var = tk.StringVar(value="毫米（mm）")
        self.material_var = tk.StringVar(value="钢")
        self.custom_material_var = tk.StringVar()
        self.custom_density_var = tk.StringVar()
        self.volume_result_var = tk.StringVar(value="等待计算")
        self.unit_weight_result_var = tk.StringVar(value="等待计算")
        self.batch_weight_result_var = tk.StringVar(value="等待计算")
        self.summary_var = tk.StringVar(value="总数量：0    总重量：0.000 kg")
        self.edit_hint_var = tk.StringVar(value="双击清单中的零件，或点击“修改选中项”进行修改。")

    def _create_widgets(self):
        header = ttk.Frame(self.root, padding=(20, 16, 20, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            header,
            text=f"机械零件重量计算器 V{weight_calculator.VERSION}",
            style="Header.TLabel",
        ).pack(side="left")
        ttk.Label(header, text="输入参数，快速计算并汇总零件重量").pack(
            side="right", pady=(8, 0)
        )

        content = ttk.Frame(self.root, padding=(20, 8, 20, 20))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0, minsize=365)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._create_input_panel(content)
        self._create_results_panel(content)

    def _create_input_panel(self, parent):
        self.input_panel = ttk.LabelFrame(parent, text="零件参数", padding=10)
        self.input_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.input_panel.columnconfigure(0, weight=1)
        self.input_panel.rowconfigure(0, weight=1)
        self.input_canvas = tk.Canvas(self.input_panel, width=320, highlightthickness=0)
        self.input_canvas.grid(row=0, column=0, sticky="nsew")
        input_scrollbar = ttk.Scrollbar(
            self.input_panel, orient="vertical", command=self.input_canvas.yview
        )
        input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_canvas.configure(yscrollcommand=input_scrollbar.set)
        panel = self.input_body = ttk.Frame(self.input_canvas)
        input_window = self.input_canvas.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _event: self.input_canvas.configure(
            scrollregion=self.input_canvas.bbox("all")
        ))
        self.input_canvas.bind("<Configure>", lambda event: self.input_canvas.itemconfigure(
            input_window, width=event.width
        ))
        self.root.bind("<MouseWheel>", self._scroll_inputs)
        panel.columnconfigure(1, weight=1)

        self._add_labeled_entry(panel, 0, "零件名称", self.part_name_var)
        self._add_labeled_entry(panel, 1, "数量", self.quantity_var)

        ttk.Label(panel, text="零件类型").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=6
        )
        part_type_box = ttk.Combobox(
            panel,
            textvariable=self.part_type_var,
            values=tuple(PART_TYPES),
            state="readonly",
        )
        part_type_box.grid(row=2, column=1, sticky="ew", pady=6)
        part_type_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._refresh_dimension_fields()
        )

        ttk.Label(panel, text="尺寸单位").grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=6
        )
        ttk.Combobox(
            panel,
            textvariable=self.unit_var,
            values=tuple(UNITS),
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", pady=6)

        self.dimensions_frame = ttk.LabelFrame(panel, text="尺寸", padding=10)
        self.dimensions_frame.grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 10)
        )
        self.dimensions_frame.columnconfigure(1, weight=1)

        ttk.Label(panel, text="材料").grid(
            row=5, column=0, sticky="w", padx=(0, 10), pady=6
        )
        material_box = ttk.Combobox(
            panel,
            textvariable=self.material_var,
            values=tuple(MATERIALS_BY_NAME) + (CUSTOM_MATERIAL,),
            state="readonly",
        )
        material_box.grid(row=5, column=1, sticky="ew", pady=6)
        material_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._toggle_custom_material_fields(),
        )

        self.custom_material_frame = ttk.Frame(panel)
        self.custom_material_frame.grid(
            row=6, column=0, columnspan=2, sticky="ew"
        )
        self.custom_material_frame.columnconfigure(1, weight=1)
        self._add_labeled_entry(
            self.custom_material_frame,
            0,
            "材料名称",
            self.custom_material_var,
        )
        self._add_labeled_entry(
            self.custom_material_frame,
            1,
            "密度 (g/cm³)",
            self.custom_density_var,
        )

        button_frame = ttk.Frame(panel)
        button_frame.grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(16, 0)
        )
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        self.submit_button = ttk.Button(
            button_frame,
            text="计算并添加",
            command=self._calculate_and_add,
            style="Primary.TButton",
        )
        self.submit_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.reset_button = ttk.Button(
            button_frame, text="清空输入", command=self._clear_inputs
        )
        self.reset_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ttk.Label(panel, textvariable=self.edit_hint_var, wraplength=310).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.parameter_widgets = [
            widget for row in range(2, 7) for widget in panel.grid_slaves(row=row)
        ]

    def _create_results_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="计算结果与零件清单", padding=16)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        result_frame = ttk.Frame(panel, padding=(12, 8))
        result_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        result_frame.columnconfigure((0, 1, 2), weight=1)

        for column, (title, variable) in enumerate(
            (
                ("体积", self.volume_result_var),
                ("单件重量", self.unit_weight_result_var),
                ("批次重量", self.batch_weight_result_var),
            )
        ):
            box = ttk.Frame(result_frame, padding=6)
            box.grid(row=0, column=column, sticky="ew")
            ttk.Label(box, text=title, style="ResultTitle.TLabel").pack()
            ttk.Label(box, textvariable=variable, style="ResultValue.TLabel").pack(
                pady=(4, 0)
            )

        table_frame = ttk.Frame(panel)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("name", "material", "quantity", "unit_weight", "total")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="extended"
        )
        self.tree.bind("<Double-1>", self._on_double_click)
        headings = {
            "name": "零件名称",
            "material": "材料",
            "quantity": "数量",
            "unit_weight": "单件重量 (kg)",
            "total": "总重量 (kg)",
        }
        widths = {
            "name": 150,
            "material": 95,
            "quantity": 65,
            "unit_weight": 120,
            "total": 120,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            anchor = "center" if column != "name" else "w"
            self.tree.column(column, width=widths[column], anchor=anchor)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(xscrollcommand=horizontal_scrollbar.set)
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        footer = ttk.Frame(panel)
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer, textvariable=self.summary_var, style="ResultValue.TLabel"
        ).grid(row=0, column=0, sticky="w")

        action_frame = ttk.Frame(footer)
        action_frame.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(
            action_frame, text="修改选中项", command=self._edit_selected
        ).pack(side="left", padx=(0, 4))
        ttk.Button(
            action_frame, text="删除选中项", command=self._delete_selected
        ).pack(side="left", padx=4)
        ttk.Button(
            action_frame, text="清空清单", command=self._clear_records
        ).pack(side="left", padx=4)
        file_frame = ttk.Frame(footer)
        file_frame.grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Button(
            file_frame, text="打开清单", command=self._open_project
        ).pack(side="left", padx=(0, 4))
        ttk.Button(
            file_frame, text="保存清单", command=self._save_project
        ).pack(side="left", padx=4)
        ttk.Button(
            file_frame,
            text="导出 CSV",
            command=self._export_csv,
            style="Primary.TButton",
        ).pack(side="left", padx=(4, 0))

    @staticmethod
    def _add_labeled_entry(parent, row, label_text, variable):
        ttk.Label(parent, text=label_text).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=6
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        return entry

    def _refresh_dimension_fields(self):
        for widget in self.dimensions_frame.winfo_children():
            widget.destroy()

        self.dimension_entries = {}
        fields = DIMENSION_FIELDS[self.part_type_var.get()]
        for row, (field_key, field_label) in enumerate(fields):
            ttk.Label(self.dimensions_frame, text=field_label).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=5
            )
            entry = ttk.Entry(self.dimensions_frame)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            self.dimension_entries[field_key] = entry

    def _toggle_custom_material_fields(self):
        if self.material_var.get() == CUSTOM_MATERIAL:
            self.custom_material_frame.grid()
        else:
            self.custom_material_frame.grid_remove()

    def _scroll_inputs(self, event):
        if event.widget is self.input_canvas or str(event.widget).startswith(str(self.input_body) + "."):
            self.input_canvas.yview_scroll(-int(event.delta / 120), "units")
            return "break"

    def _calculate_and_add(self):
        dimension_values = {
            key: entry.get() for key, entry in self.dimension_entries.items()
        }

        try:
            if self.legacy_edit:
                name = self.part_name_var.get().strip()
                if not name:
                    raise ValueError("零件名称不能为空。")
                original = self.records[self.tree.index(self.editing_item)]
                record = weight_calculator.create_part_record(
                    name, original["material_name"],
                    parse_positive_integer(self.quantity_var.get()), original["unit_weight_kg"],
                )
                record = weight_calculator._validate_project_record(record, 1)
                calculation = {"record": record, "volume_cm3": None}
            else:
                calculation = calculate_part_from_inputs(
                    self.part_name_var.get(),
                    self.quantity_var.get(),
                    self.part_type_var.get(),
                    self.unit_var.get(),
                    dimension_values,
                    self.material_var.get(),
                    self.custom_material_var.get(),
                    self.custom_density_var.get(),
                )
        except (ValueError, OverflowError) as error:
            messagebox.showerror("输入错误", str(error), parent=self.root)
            return False

        record = calculation["record"]
        if self.editing_item is None:
            self.records.append(record)
            self.tree.insert("", "end", values=self._record_values(record))
        else:
            item = self.editing_item
            self.records[self.tree.index(item)] = record
            self.tree.item(item, values=self._record_values(record))
            self.tree.selection_set(item)
            self.tree.see(item)
            self._reset_inputs()

        volume = calculation["volume_cm3"]
        self.volume_result_var.set("未保存尺寸" if volume is None else f"{volume:.2f} cm³")
        self.unit_weight_result_var.set(
            f"{record['unit_weight_kg']:.3f} kg"
        )
        self.batch_weight_result_var.set(
            f"{record['total_weight_kg']:.3f} kg"
        )
        self.has_unsaved_changes = True
        self._refresh_summary()
        return True

    @staticmethod
    def _record_values(record):
        return (
            record["name"], record["material_name"], record["quantity"],
            f"{record['unit_weight_kg']:.3f}", f"{record['total_weight_kg']:.3f}",
        )

    def _form_state(self):
        return (
            self.part_name_var.get(), self.quantity_var.get(),
            self.part_type_var.get(), self.unit_var.get(), self.material_var.get(),
            self.custom_material_var.get(), self.custom_density_var.get(),
            {key: entry.get() for key, entry in self.dimension_entries.items()},
        )

    def _edit_has_changes(self):
        return self.editing_item is not None and self._form_state() != self.edit_baseline

    def _confirm_discard_edit(self):
        return not self._edit_has_changes() or messagebox.askyesno(
            "尚未更新的零件", "当前零件的修改尚未更新到清单，确定要放弃这些修改吗？",
            parent=self.root,
        )

    def _resolve_pending_edit(self):
        if not self._edit_has_changes():
            return True
        answer = messagebox.askyesnocancel(
            "尚未更新的零件",
            "当前零件的修改尚未更新到清单。是否先更新再继续？\n\n"
            "选择“是”更新，选择“否”放弃修改，选择“取消”返回编辑。",
            parent=self.root,
        )
        if answer is None:
            return False
        if answer:
            return self._calculate_and_add()
        self._reset_inputs()
        return True

    def _on_double_click(self, event):
        if self.tree.identify_region(event.x, event.y) not in ("cell", "tree"):
            return
        item = self.tree.identify_row(event.y)
        if item:
            self._edit_selected(item)
            return "break"

    def _edit_selected(self, item=None):
        if item is None:
            selection = self.tree.selection()
            if len(selection) != 1:
                messagebox.showinfo("修改零件", "请在清单中选择一个要修改的零件。", parent=self.root)
                return
            item = selection[0]
        if item == self.editing_item or not self._confirm_discard_edit():
            return
        record = self.records[self.tree.index(item)]
        self._reset_inputs()
        self.editing_item = item
        self.tree.selection_set(item)
        self.part_name_var.set(record["name"])
        self.quantity_var.set(str(record["quantity"]))
        inputs = record.get("inputs")
        self.legacy_edit = inputs is None
        self.input_panel.configure(text="修改零件")
        self.reset_button.configure(text="取消修改")
        if inputs is None:
            for widget in self.parameter_widgets:
                widget.grid_remove()
            self.submit_button.configure(text="更新名称和数量")
            self.edit_hint_var.set(
                f"正在修改：{record['name']}\n旧版记录未保存尺寸，仅可修改名称和数量。"
                "材料与单件重量保持原值。"
            )
        else:
            self.part_type_var.set(next(name for name, code in PART_TYPES.items() if code == inputs["part_type"]))
            self.unit_var.set(next(name for name, code in UNIT_CODES.items() if code == inputs["unit"]))
            self._refresh_dimension_fields()
            for key, value in inputs["dimensions"].items():
                self.dimension_entries[key].insert(0, str(value))
            self.material_var.set(CUSTOM_MATERIAL if inputs["custom_material"] else record["material_name"])
            if inputs["custom_material"]:
                self.custom_material_var.set(record["material_name"])
                self.custom_density_var.set(str(inputs["density_g_per_cm3"]))
            self._toggle_custom_material_fields()
            self.submit_button.configure(text="计算并更新")
            self.edit_hint_var.set(f"正在修改：{record['name']}\n点击“计算并更新”替换原记录，点击“取消修改”放弃。")
        self.edit_baseline = self._form_state()
        self.input_canvas.yview_moveto(0)

    def _clear_inputs(self):
        if self._confirm_discard_edit():
            self._reset_inputs()

    def _reset_inputs(self):
        self.editing_item = None
        self.edit_baseline = None
        self.legacy_edit = False
        self.input_panel.configure(text="零件参数")
        self.submit_button.configure(text="计算并添加")
        self.reset_button.configure(text="清空输入")
        self.edit_hint_var.set("双击清单中的零件，或点击“修改选中项”进行修改。")
        for widget in self.parameter_widgets:
            widget.grid()
        self.part_name_var.set("")
        self.quantity_var.set("1")
        self.part_type_var.set("实心圆柱")
        self.unit_var.set("毫米（mm）")
        self.material_var.set("钢")
        self.custom_material_var.set("")
        self.custom_density_var.set("")
        self._refresh_dimension_fields()
        self._toggle_custom_material_fields()
        self.input_canvas.yview_moveto(0)

    def _delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "删除零件", "请先在清单中选择要删除的零件。", parent=self.root
            )
            return

        selected_indices = sorted(
            (self.tree.index(item) for item in selected_items), reverse=True
        )
        if self.editing_item in selected_items:
            if not self._confirm_discard_edit():
                return
            self._reset_inputs()
        for index in selected_indices:
            del self.records[index]
        for item in selected_items:
            self.tree.delete(item)

        self.has_unsaved_changes = True
        self._refresh_summary()

    def _clear_records(self):
        if not self.records:
            messagebox.showinfo(
                "清空清单", "当前清单已经是空的。", parent=self.root
            )
            return

        should_clear = messagebox.askyesno(
            "清空清单", "确定要清空全部零件记录吗？", parent=self.root
        )
        if not should_clear:
            return

        self._reset_inputs()
        self.records.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.has_unsaved_changes = True
        self._refresh_summary()

    def _refresh_summary(self):
        total_quantity, total_weight_kg = (
            weight_calculator.calculate_summary_totals(self.records)
        )
        self.summary_var.set(
            f"总数量：{total_quantity}    总重量：{total_weight_kg:.3f} kg"
        )

    def _refresh_records_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in self.records:
            self.tree.insert("", "end", values=self._record_values(record))

        self._refresh_summary()

    def _open_project(self):
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="打开零件清单",
            filetypes=(
                ("机械零件清单", "*.mpwc"),
                ("所有文件", "*.*"),
            ),
        )
        if not file_path:
            return

        if not self._resolve_pending_edit():
            return
        if self.has_unsaved_changes:
            should_open = messagebox.askyesno(
                "未保存的修改",
                "当前清单有尚未保存的修改，继续打开会丢失这些修改。\n\n"
                "确定要继续吗？",
                parent=self.root,
            )
            if not should_open:
                return

        try:
            loaded_records = weight_calculator.load_project_file(file_path)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "打开失败", f"无法打开清单文件：{error}", parent=self.root
            )
            return

        self.records = loaded_records
        self._reset_inputs()
        self.current_project_path = Path(file_path).resolve()
        self.has_unsaved_changes = False
        self._refresh_records_table()
        self.volume_result_var.set("等待计算")
        self.unit_weight_result_var.set("等待计算")
        self.batch_weight_result_var.set("等待计算")
        messagebox.showinfo(
            "打开成功",
            f"已打开零件清单：\n{self.current_project_path}",
            parent=self.root,
        )

    def _save_project(self):
        if not self._resolve_pending_edit():
            return
        if not self.records:
            messagebox.showinfo(
                "保存清单", "请先计算并添加至少一个零件。", parent=self.root
            )
            return

        file_path = self.current_project_path
        if file_path is None:
            default_name = datetime.now().strftime(
                "weight_project_%Y%m%d_%H%M%S.mpwc"
            )
            selected_path = filedialog.asksaveasfilename(
                parent=self.root,
                title="保存零件清单",
                defaultextension=".mpwc",
                initialfile=default_name,
                filetypes=(
                    ("机械零件清单", "*.mpwc"),
                    ("所有文件", "*.*"),
                ),
            )
            if not selected_path:
                return
            file_path = Path(selected_path)

        try:
            saved_path = weight_calculator.save_project_file(
                self.records, file_path
            )
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "保存失败", f"清单文件保存失败：{error}", parent=self.root
            )
            return

        self.current_project_path = saved_path
        self.has_unsaved_changes = False
        messagebox.showinfo(
            "保存成功",
            f"零件清单已保存：\n{saved_path}",
            parent=self.root,
        )

    def _export_csv(self):
        if not self._resolve_pending_edit():
            return
        if not self.records:
            messagebox.showinfo(
                "导出 CSV", "请先计算并添加至少一个零件。", parent=self.root
            )
            return

        default_name = datetime.now().strftime("weight_summary_%Y%m%d_%H%M%S.csv")
        file_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="保存零件清单",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=(("CSV 文件", "*.csv"), ("所有文件", "*.*")),
        )
        if not file_path:
            return

        try:
            saved_path = weight_calculator.export_records_to_csv_file(
                self.records, file_path
            )
        except OSError as error:
            messagebox.showerror(
                "保存失败", f"CSV 文件保存失败：{error}", parent=self.root
            )
            return

        messagebox.showinfo(
            "导出成功", f"CSV 文件已保存：\n{saved_path}", parent=self.root
        )

    def _on_close(self):
        if not self._resolve_pending_edit():
            return
        if self.has_unsaved_changes:
            should_close = messagebox.askyesno(
                "确认退出",
                "当前零件清单有尚未保存的修改，确定要关闭软件吗？",
                parent=self.root,
            )
            if not should_close:
                return

        self.root.destroy()


def main():
    root = tk.Tk()
    WeightCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

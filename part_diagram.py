"""Canvas illustrations that explain dimensions; no numerical inputs or calculations."""
import tkinter as tk


class PartDiagram(tk.Canvas):
    DRAWING_WIDTH = 420
    DRAWING_HEIGHT = 175
    OUTLINE = "#456b91"
    DIMENSION = "#235e91"
    HOLE_DIMENSION = "#8752a1"

    def __init__(self, parent):
        super().__init__(parent, width=420, height=125, background="#f8fbff", highlightthickness=0)
        self.part_type = None
        self._scale = 1
        self._offset = (0, 0)
        self.bind("<Configure>", lambda _event: self._redraw())

    def set_part_type(self, part_type):
        if part_type not in (None, "solid_cylinder", "hollow_cylinder", "rectangular_prism"):
            raise ValueError("未知的示意图类型。")
        self.part_type = part_type
        self._redraw()

    def _coordinates(self, coordinates):
        return [
            value * self._scale + self._offset[index % 2]
            for index, value in enumerate(coordinates)
        ]

    def _line(self, *coordinates, color=None, arrow=False, tags=()):
        options = dict(fill=color or self.DIMENSION, width=max(1, 1.5 * self._scale), tags=tags)
        if arrow:
            options.update(arrow=tk.BOTH, arrowshape=tuple(value * self._scale for value in (7, 8, 3)))
        self.create_line(*self._coordinates(coordinates), **options)

    def _shape(self, kind, coordinates, fill):
        getattr(self, "create_" + kind)(
            *self._coordinates(coordinates), fill=fill, outline=self.OUTLINE,
            width=max(1, 1.5 * self._scale), tags=("part", "part:" + self.part_type),
        )

    def _dimension(self, key, label, endpoints, label_position, color=None):
        color = color or self.DIMENSION
        self._line(*endpoints, color=color, arrow=True, tags=("dimension", "dimension:" + key))
        self.create_text(
            *self._coordinates(label_position), text=label, fill=color,
            font=("Microsoft YaHei UI", -max(14, round(15 * self._scale)), "bold"),
            tags=("dimension_label", "dimension_label:" + key),
        )

    def _redraw(self):
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1:
            width = int(self.cget("width"))
        if height <= 1:
            height = int(self.cget("height"))
        self._scale = min(width / self.DRAWING_WIDTH, height / self.DRAWING_HEIGHT)
        self._offset = (
            (width - self.DRAWING_WIDTH * self._scale) / 2,
            (height - self.DRAWING_HEIGHT * self._scale) / 2,
        )
        self.delete("all")
        if self.part_type is None:
            self.create_text(
                width / 2, height / 2, text="该记录未保存形状和尺寸\n无法显示对应的尺寸示意图",
                width=max(1, width - 30), justify="center", fill="#657587",
                font=("Microsoft YaHei UI", -14), tags="unavailable",
            )
        elif self.part_type == "rectangular_prism":
            self._draw_block()
        else:
            self._draw_cylinder(hollow=self.part_type == "hollow_cylinder")

    def _draw_cylinder(self, hollow):
        self._shape("oval", (285, 55, 325, 125), "#b7d0e7")
        self._shape("polygon", (120, 55, 305, 55, 305, 125, 120, 125), "#d9e8f5")
        # The join at the rear is inside the curved end face, not an exposed edge.
        self._line(305, 57, 305, 123, color="#d9e8f5")
        self._shape("oval", (100, 55, 140, 125), "#edf5fc")
        self._line(72, 55, 120, 55)
        self._line(72, 125, 120, 125)
        self._dimension(
            "outer_diameter" if hollow else "diameter", "外径" if hollow else "直径",
            (72, 55, 72, 125), (45, 90),
        )
        if hollow:
            self._shape("oval", (109, 70, 131, 110), "#f8fbff")
            self._line(120, 70, 159, 70, color=self.HOLE_DIMENSION)
            self._line(120, 110, 159, 110, color=self.HOLE_DIMENSION)
            self._dimension("inner_diameter", "内径", (159, 70, 159, 110), (187, 90), self.HOLE_DIMENSION)
        self._line(120, 130, 120, 150)
        self._line(305, 130, 305, 150)
        self._dimension("length", "长度", (120, 147, 305, 147), (212, 159))

    def _draw_block(self):
        self._shape("polygon", (105, 75, 150, 45, 320, 45, 275, 75), "#edf5fc")
        self._shape("polygon", (275, 75, 320, 45, 320, 95, 275, 125), "#b7d0e7")
        self._shape("polygon", (105, 75, 275, 75, 275, 125, 105, 125), "#d9e8f5")
        self._line(105, 130, 105, 151)
        self._line(275, 130, 275, 151)
        self._dimension("length", "长度", (105, 147, 275, 147), (190, 159))
        self._line(105, 75, 77, 57)
        self._line(150, 45, 122, 27)
        self._dimension("width", "宽度", (77, 57, 122, 27), (68, 30))
        self._line(325, 45, 350, 45)
        self._line(325, 95, 350, 95)
        self._dimension("height", "高度", (345, 45, 345, 95), (373, 70))

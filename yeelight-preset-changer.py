import colorsys
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from miio import Device

DEFAULT_IP = ""
DEFAULT_TOKEN = ""


def kelvin_to_rgb(kelvin):
    temp = kelvin / 100.0
    if temp <= 66:
        r = 255
    else:
        r = max(0, min(255, 329.698727446 * ((temp - 60) ** -0.1332047592)))

    if temp <= 66:
        g = max(0, min(255, 99.4708025861 * (max(1, temp) ** 0.3) - 30))
    else:
        g = max(0, min(255, 288.1221695283 * ((temp - 60) ** -0.0755148492)))

    if temp >= 66:
        b = 255
    elif temp <= 19:
        b = 0
    else:
        b = max(
            0, min(255, 138.5177312231 * (max(1, temp - 10) ** 0.5) - 305.0447927307)
        )

    return int(r), int(g), int(b)


def rgb_to_hwb(r, g, b):
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    w = min(rf, gf, bf)
    v = max(rf, gf, bf)
    black = 1.0 - v
    h, _, _ = colorsys.rgb_to_hsv(rf, gf, bf)
    return round(h * 360, 1), round(w * 100, 1), round(black * 100, 1)


class AdvancedColorDialog(tk.Toplevel):
    def __init__(self, parent, initial_rgb=(255, 0, 0)):
        super().__init__(parent)
        self.title("色彩高级数值编辑")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.r, self.g, self.b = initial_rgb
        self.result = None
        self._syncing = False

        self._build_ui()
        self._update_all_from_rgb()

    def _build_ui(self):
        self.preview = tk.Canvas(self, height=65, relief="solid", bd=1)
        self.preview.pack(fill="x", padx=16, pady=(12, 8))

        btn_box = ttk.Frame(self)
        btn_box.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Button(
            btn_box, text="打开系统拾色器 (Color Picker)", command=self._pick_color
        ).pack(fill="x")

        form = ttk.LabelFrame(
            self, text="数值格式（支持直接修改 HEX 与 RGB）", padding=(15, 10)
        )
        form.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        form.columnconfigure(0, weight=0)
        form.columnconfigure(1, weight=1)

        self.hex_var = tk.StringVar()
        self.rgb_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.hsv_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.hsl_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self.hwb_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar()]

        # HEX
        ttk.Label(form, text="HEX", width=14, anchor="w").grid(
            row=0, column=0, sticky="w", pady=5
        )
        hex_cell = ttk.Frame(form)
        hex_cell.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(hex_cell, text="#").pack(side="left", padx=(0, 2))
        ttk.Entry(hex_cell, textvariable=self.hex_var, width=12).pack(side="left")

        # RGB
        ttk.Label(form, text="RGB (0-255)", width=14, anchor="w").grid(
            row=1, column=0, sticky="w", pady=5
        )
        rgb_cell = ttk.Frame(form)
        rgb_cell.grid(row=1, column=1, sticky="ew", pady=5)
        for idx, (label, var) in enumerate(zip(["R:", "G:", "B:"], self.rgb_vars)):
            ttk.Label(rgb_cell, text=label).pack(
                side="left", padx=(0 if idx == 0 else 10, 2)
            )
            ttk.Entry(rgb_cell, textvariable=var, width=6).pack(side="left")

        # HSV
        ttk.Label(form, text="HSV", width=14, anchor="w").grid(
            row=2, column=0, sticky="w", pady=5
        )
        hsv_cell = ttk.Frame(form)
        hsv_cell.grid(row=2, column=1, sticky="ew", pady=5)
        for idx, (label, var, unit) in enumerate(
            zip(["H:", "S:", "V:"], self.hsv_vars, ["°", "%", "%"])
        ):
            ttk.Label(hsv_cell, text=label).pack(
                side="left", padx=(0 if idx == 0 else 8, 2)
            )
            ttk.Entry(hsv_cell, textvariable=var, width=6, state="readonly").pack(
                side="left"
            )
            ttk.Label(hsv_cell, text=unit).pack(side="left", padx=(1, 0))

        # HSL
        ttk.Label(form, text="HSL", width=14, anchor="w").grid(
            row=3, column=0, sticky="w", pady=5
        )
        hsl_cell = ttk.Frame(form)
        hsl_cell.grid(row=3, column=1, sticky="ew", pady=5)
        for idx, (label, var, unit) in enumerate(
            zip(["H:", "S:", "L:"], self.hsl_vars, ["°", "%", "%"])
        ):
            ttk.Label(hsl_cell, text=label).pack(
                side="left", padx=(0 if idx == 0 else 8, 2)
            )
            ttk.Entry(hsl_cell, textvariable=var, width=6, state="readonly").pack(
                side="left"
            )
            ttk.Label(hsl_cell, text=unit).pack(side="left", padx=(1, 0))

        # HWB
        ttk.Label(form, text="HWB", width=14, anchor="w").grid(
            row=4, column=0, sticky="w", pady=5
        )
        hwb_cell = ttk.Frame(form)
        hwb_cell.grid(row=4, column=1, sticky="ew", pady=5)
        for idx, (label, var, unit) in enumerate(
            zip(["H:", "W:", "B:"], self.hwb_vars, ["°", "%", "%"])
        ):
            ttk.Label(hwb_cell, text=label).pack(
                side="left", padx=(0 if idx == 0 else 8, 2)
            )
            ttk.Entry(hwb_cell, textvariable=var, width=6, state="readonly").pack(
                side="left"
            )
            ttk.Label(hwb_cell, text=unit).pack(side="left", padx=(1, 0))

        self.hex_var.trace_add("write", lambda *_: self._parse_hex())
        for v in self.rgb_vars:
            v.trace_add("write", lambda *_: self._parse_rgb())

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=16, pady=(0, 14))
        ttk.Button(bottom, text="应用色彩", command=self._confirm).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(bottom, text="取消", command=self.destroy).pack(side="right")

    def _update_all_from_rgb(self):
        if self._syncing:
            return
        self._syncing = True

        r, g, b = self.r, self.g, self.b
        hex_val = f"{r:02X}{g:02X}{b:02X}"
        self.preview.config(bg=f"#{hex_val}")

        self.hex_var.set(hex_val)
        self.rgb_vars[0].set(str(r))
        self.rgb_vars[1].set(str(g))
        self.rgb_vars[2].set(str(b))

        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self.hsv_vars[0].set(f"{round(h * 360, 1)}")
        self.hsv_vars[1].set(f"{round(s * 100, 1)}")
        self.hsv_vars[2].set(f"{round(v * 100, 1)}")

        h_l, l, s_l = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        self.hsl_vars[0].set(f"{round(h_l * 360, 1)}")
        self.hsl_vars[1].set(f"{round(s_l * 100, 1)}")
        self.hsl_vars[2].set(f"{round(l * 100, 1)}")

        hw, hb, h_blk = rgb_to_hwb(r, g, b)
        self.hwb_vars[0].set(f"{hw}")
        self.hwb_vars[1].set(f"{hb}")
        self.hwb_vars[2].set(f"{h_blk}")

        self._syncing = False

    def _parse_hex(self):
        if self._syncing:
            return
        raw = self.hex_var.get().strip().lstrip("#")
        if len(raw) == 6:
            try:
                self.r, self.g, self.b = (
                    int(raw[0:2], 16),
                    int(raw[2:4], 16),
                    int(raw[4:6], 16),
                )
                self.preview.config(bg=f"#{raw}")
                self._syncing = True
                self.rgb_vars[0].set(str(self.r))
                self.rgb_vars[1].set(str(self.g))
                self.rgb_vars[2].set(str(self.b))
                self._sync_readonly()
                self._syncing = False
            except ValueError:
                pass

    def _parse_rgb(self):
        if self._syncing:
            return
        try:
            r = int(self.rgb_vars[0].get().strip())
            g = int(self.rgb_vars[1].get().strip())
            b = int(self.rgb_vars[2].get().strip())
            if all(0 <= c <= 255 for c in (r, g, b)):
                self.r, self.g, self.b = r, g, b
                self.preview.config(bg=f"#{r:02X}{g:02X}{b:02X}")
                self._syncing = True
                self.hex_var.set(f"{r:02X}{g:02X}{b:02X}")
                self._sync_readonly()
                self._syncing = False
        except ValueError:
            pass

    def _sync_readonly(self):
        r, g, b = self.r, self.g, self.b
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self.hsv_vars[0].set(f"{round(h * 360, 1)}")
        self.hsv_vars[1].set(f"{round(s * 100, 1)}")
        self.hsv_vars[2].set(f"{round(v * 100, 1)}")

        h_l, l, s_l = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        self.hsl_vars[0].set(f"{round(h_l * 360, 1)}")
        self.hsl_vars[1].set(f"{round(s_l * 100, 1)}")
        self.hsl_vars[2].set(f"{round(l * 100, 1)}")

        hw, hb, h_blk = rgb_to_hwb(r, g, b)
        self.hwb_vars[0].set(f"{hw}")
        self.hwb_vars[1].set(f"{hb}")
        self.hwb_vars[2].set(f"{h_blk}")

    def _pick_color(self):
        res = colorchooser.askcolor(
            color=f"#{self.r:02X}{self.g:02X}{self.b:02X}", parent=self
        )
        if res[0]:
            self.r, self.g, self.b = [int(c) for c in res[0]]
            self._update_all_from_rgb()

    def _confirm(self):
        self.result = (self.r << 16) | (self.g << 8) | self.b
        self.destroy()


class LampConfigMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("米家/Yeelight 床头灯 模式键配置工具")
        self.root.geometry("760x860")
        self.root.minsize(720, 750)

        self.cts = [1700, 3200, 5000, 6400]
        self.colors = [16711680, 16776960, 65280, 65535, 255, 16711935]

        self.selected_ct_idx = tk.IntVar(value=0)
        self.selected_color_idx = tk.IntVar(value=0)

        self._build_header()
        self._build_footer()
        self._build_body()

        self.refresh_ct_ui()
        self.refresh_color_ui()

    def _get_dev(self):
        ip = self.ip_var.get().strip()
        tok = self.token_var.get().strip()
        if not ip or not tok:
            raise ValueError("请填入有效的 IP 和 Token")
        return Device(ip, tok)

    def _build_header(self):
        f = ttk.LabelFrame(self.root, text="网络通信设置", padding=(12, 8))
        f.pack(fill="x", padx=15, pady=(10, 5))

        # 配置 Grid 列权重：让 Token 输入框（列 3）弹性自适应拉伸
        f.columnconfigure(0, weight=0)
        f.columnconfigure(1, weight=0)
        f.columnconfigure(2, weight=0)
        f.columnconfigure(3, weight=1)
        f.columnconfigure(4, weight=0)

        # IP
        ttk.Label(f, text="IP 地址:").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        self.ip_var = tk.StringVar(value=DEFAULT_IP)
        ttk.Entry(f, textvariable=self.ip_var, width=15).grid(row=0, column=1, sticky="w", padx=(0, 12), pady=4)

        # Token
        ttk.Label(f, text="Token:").grid(row=0, column=2, sticky="w", padx=(0, 4), pady=4)
        self.token_var = tk.StringVar(value=DEFAULT_TOKEN)
        ttk.Entry(f, textvariable=self.token_var).grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=4)

        # 读取按钮：显式设置 padding 防止 macOS 暗色控件截断文字
        ttk.Button(
            f, 
            text="读取设置 (get_ps)", 
            command=self.load_from_lamp,
            padding=(10, 4)
        ).grid(row=0, column=4, sticky="e", pady=4)

    def _build_footer(self):
        btn_frame = ttk.Frame(self.root, padding=12)
        btn_frame.pack(fill="x", side="bottom")

        btn = ttk.Button(
            btn_frame,
            text="保存到设备 (set_ps)",
            command=self.save_to_lamp,
        )
        btn.pack(fill="x")

    def _build_body(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=15, pady=5)

        # 色温区域
        self.ct_frame = ttk.LabelFrame(
            container, text="常用色温配置 (限制 2 - 4 个 | 1700K - 6500K)", padding=10
        )
        self.ct_frame.pack(fill="x", pady=6)

        ct_ctrl = ttk.Frame(self.ct_frame)
        ct_ctrl.pack(fill="x", pady=2)

        self.ct_count_lbl = ttk.Label(ct_ctrl, text="", font=("", 10, "bold"))
        self.ct_count_lbl.pack(side="left", padx=4)

        self.btn_ct_add = ttk.Button(ct_ctrl, text="➕ 增加色温", command=self.add_ct)
        self.btn_ct_add.pack(side="left", padx=5)

        self.btn_ct_remove = ttk.Button(
            ct_ctrl, text="➖ 移除选中项", command=self.remove_selected_ct
        )
        self.btn_ct_remove.pack(side="left", padx=5)

        self.ct_container = ttk.Frame(self.ct_frame)
        self.ct_container.pack(fill="x", expand=True, pady=6)

        # 色彩区域
        self.color_frame = ttk.LabelFrame(
            container, text="常用色彩配置 (限制 2 - 7 个 | 完整色彩空间)", padding=10
        )
        self.color_frame.pack(fill="both", expand=True, pady=6)

        col_ctrl = ttk.Frame(self.color_frame)
        col_ctrl.pack(fill="x", pady=2)

        self.color_count_lbl = ttk.Label(col_ctrl, text="", font=("", 10, "bold"))
        self.color_count_lbl.pack(side="left", padx=4)

        self.btn_col_add = ttk.Button(
            col_ctrl, text="➕ 增加色彩", command=self.add_color
        )
        self.btn_col_add.pack(side="left", padx=5)

        self.btn_col_remove = ttk.Button(
            col_ctrl, text="➖ 移除选中项", command=self.remove_selected_color
        )
        self.btn_col_remove.pack(side="left", padx=5)

        self.color_container = ttk.Frame(self.color_frame)
        self.color_container.pack(fill="both", expand=True, pady=6)

    def refresh_ct_ui(self):
        for w in self.ct_container.winfo_children():
            w.destroy()

        count = len(self.cts)
        self.ct_count_lbl.config(text=f"当前槽位: {count}/4")
        self.btn_ct_add.config(state="normal" if count < 4 else "disabled")
        self.btn_ct_remove.config(state="normal" if count > 2 else "disabled")

        if self.selected_ct_idx.get() >= count:
            self.selected_ct_idx.set(max(0, count - 1))

        for idx, k in enumerate(self.cts):
            row = ttk.Frame(self.ct_container)
            row.pack(fill="x", pady=4)

            rb = ttk.Radiobutton(
                row, text=f"顺序 {idx+1}", value=idx, variable=self.selected_ct_idx
            )
            rb.pack(side="left", padx=(4, 8))

            r, g, b = kelvin_to_rgb(k)
            canvas = tk.Canvas(
                row,
                width=36,
                height=22,
                bg=f"#{r:02x}{g:02x}{b:02x}",
                bd=1,
                relief="solid",
            )
            canvas.pack(side="left", padx=6)

            k_var = tk.StringVar(value=str(k))
            scale = ttk.Scale(row, from_=1700, to=6500, value=k)
            scale.pack(side="left", fill="x", expand=True, padx=8)

            entry = ttk.Entry(row, textvariable=k_var, width=6)
            entry.pack(side="left", padx=2)
            ttk.Label(row, text="K").pack(side="left", padx=(0, 8))

            def make_slider_cmd(i=idx, kv=k_var, cv=canvas):
                def cmd(v):
                    val = int(float(v))
                    self.cts[i] = val
                    kv.set(str(val))
                    cr, cg, cb = kelvin_to_rgb(val)
                    cv.config(bg=f"#{cr:02x}{cg:02x}{cb:02x}")
                    self.selected_ct_idx.set(i)

                return cmd

            def make_entry_cmd(i=idx, sc=scale, kv=k_var, cv=canvas):
                def cmd(*_):
                    try:
                        val = int(kv.get().strip())
                        if 1700 <= val <= 6500:
                            self.cts[i] = val
                            sc.set(val)
                            cr, cg, cb = kelvin_to_rgb(val)
                            cv.config(bg=f"#{cr:02x}{cg:02x}{cb:02x}")
                            self.selected_ct_idx.set(i)
                    except ValueError:
                        pass

                return cmd

            scale.config(command=make_slider_cmd())
            k_var.trace_add("write", make_entry_cmd())

    def add_ct(self):
        if len(self.cts) < 4:
            self.cts.append(4000)
            self.selected_ct_idx.set(len(self.cts) - 1)
            self.refresh_ct_ui()

    def remove_selected_ct(self):
        if len(self.cts) <= 2:
            messagebox.showwarning("数量限制", "色温模式最少需要保留 2 个槽位！")
            return
        idx = self.selected_ct_idx.get()
        if 0 <= idx < len(self.cts):
            self.cts.pop(idx)
            self.selected_ct_idx.set(max(0, idx - 1))
            self.refresh_ct_ui()

    def refresh_color_ui(self):
        for w in self.color_container.winfo_children():
            w.destroy()

        count = len(self.colors)
        self.color_count_lbl.config(text=f"当前槽位: {count}/7")
        self.btn_col_add.config(state="normal" if count < 7 else "disabled")
        self.btn_col_remove.config(state="normal" if count > 2 else "disabled")

        if self.selected_color_idx.get() >= count:
            self.selected_color_idx.set(max(0, count - 1))

        for idx, val in enumerate(self.colors):
            row = ttk.Frame(self.color_container)
            row.pack(fill="x", pady=4)

            rb = ttk.Radiobutton(
                row, text=f"顺序 {idx+1}", value=idx, variable=self.selected_color_idx
            )
            rb.pack(side="left", padx=(4, 8))

            hex_color = f"#{val:06X}"
            r = (val >> 16) & 0xFF
            g = (val >> 8) & 0xFF
            b = val & 0xFF

            canvas = tk.Canvas(
                row, width=36, height=22, bg=hex_color, bd=1, relief="solid"
            )
            canvas.pack(side="left", padx=6)

            ttk.Label(row, text=f"{hex_color}  |  RGB: ({r}, {g}, {b})", width=34).pack(
                side="left", padx=8
            )

            def make_edit_cmd(i=idx, rgb_tuple=(r, g, b)):
                def cmd():
                    self.selected_color_idx.set(i)
                    self.edit_color(i, rgb_tuple)

                return cmd

            ttk.Button(row, text="设置", command=make_edit_cmd()).pack(
                side="right", padx=5
            )

    def add_color(self):
        if len(self.colors) < 7:
            dlg = AdvancedColorDialog(self.root, initial_rgb=(255, 0, 0))
            self.root.wait_window(dlg)
            if dlg.result is not None:
                self.colors.append(dlg.result)
                self.selected_color_idx.set(len(self.colors) - 1)
                self.refresh_color_ui()

    def remove_selected_color(self):
        if len(self.colors) <= 2:
            messagebox.showwarning("数量限制", "色彩模式最少需要保留 2 个槽位！")
            return
        idx = self.selected_color_idx.get()
        if 0 <= idx < len(self.colors):
            self.colors.pop(idx)
            self.selected_color_idx.set(max(0, idx - 1))
            self.refresh_color_ui()

    def edit_color(self, index, current_rgb):
        dlg = AdvancedColorDialog(self.root, initial_rgb=current_rgb)
        self.root.wait_window(dlg)
        if dlg.result is not None:
            self.colors[index] = dlg.result
            self.refresh_color_ui()

    def load_from_lamp(self):
        try:
            dev = self._get_dev()
            ct_raw = dev.send("get_ps", ["get_mode_data", "1"])
            rgb_raw = dev.send("get_ps", ["get_mode_data", "2"])

            parsed_ct = []
            parsed_rgb = []

            if ct_raw and isinstance(ct_raw, list) and ct_raw[0]:
                parts = [int(x) for x in ct_raw[0].split(",") if x.strip().isdigit()]
                if len(parts) > 1 and parts[0] == 1:
                    parsed_ct = parts[1:]

            if rgb_raw and isinstance(rgb_raw, list) and rgb_raw[0]:
                parts = [int(x) for x in rgb_raw[0].split(",") if x.strip().isdigit()]
                if len(parts) > 1 and parts[0] == 2:
                    parsed_rgb = parts[1:]

            if parsed_ct:
                self.cts = parsed_ct
                self.selected_ct_idx.set(0)
                self.refresh_ct_ui()

            if parsed_rgb:
                self.colors = parsed_rgb
                self.selected_color_idx.set(0)
                self.refresh_color_ui()

            messagebox.showinfo(
                "读取成功",
                f"已从设备 Flash 读取配置：\n\n色温槽位 ({len(self.cts)}个): {self.cts} K\n色彩槽位 ({len(self.colors)}个): {self.colors}",
            )
        except Exception as e:
            messagebox.showerror("读取失败", f"get_ps 执行失败: {e}")

    def save_to_lamp(self):
        if not (2 <= len(self.cts) <= 4):
            messagebox.showwarning("校验失败", "色温模式数量必须为 2 到 4 个！")
            return
        if not (2 <= len(self.colors) <= 7):
            messagebox.showwarning("校验失败", "色彩模式数量必须为 2 到 7 个！")
            return

        try:
            dev = self._get_dev()

            payload_ct = "1," + ",".join(str(k) for k in self.cts)
            payload_rgb = "2," + ",".join(str(c) for c in self.colors)

            res_ct = dev.send("set_ps", ["cfg_mode_data", payload_ct])
            res_rgb = dev.send("set_ps", ["cfg_mode_data", payload_rgb])

            if res_ct == ["ok"] and res_rgb == ["ok"]:
                messagebox.showinfo(
                    "保存成功",
                    "设置已固化写入床头灯 Flash 内部记忆！\n\n现在可直接按下顶部实体模式键测试。",
                )
            else:
                messagebox.showwarning(
                    "响应提示", f"结果: 色温={res_ct}, 色彩={res_rgb}"
                )
        except Exception as e:
            messagebox.showerror("保存失败", f"set_ps 写入失败: {e}")


if __name__ == "__main__":
    tk_root = tk.Tk()
    app = LampConfigMaster(tk_root)
    tk_root.mainloop()

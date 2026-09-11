#!/usr/bin/env python3
"""
stage_rig_gui.py - simple desktop front-end for the Live Stage Toolkit.

Two tools behind one window, aimed at theatre technical staff rather than
programmers:
  * Calculator tab  - wraps stage_rig_calculator.analyse() (imported here as
    stage_math - just a local alias, this is one engine, not two files).
  * Network tab     - wraps the real Art-Net QA engine from artnet_probe.py
    (NOT a generic packet counter - it decodes Art-Net, tracks drops,
    duplicates, sender restarts and jitter per universe, exactly like the
    command-line tool).

No dependencies beyond the Python standard library, matching the rest of the
Live Stage Toolkit.

Part of the Live Stage Toolkit. MIT licence.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import json
import threading

import stage_rig_calculator as stage_math
from artnet_probe import ArtNetProbe, ARTNET_PORT


class StageRigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Инженерный калькулятор: Захват движений и Проекция")
        self.root.geometry("640x780")
        self.root.resizable(True, True)

        self._build_menu()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.calc_frame = ttk.Frame(self.notebook)
        self.probe_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.calc_frame, text="Калькулятор (Mocap & Проекция)")
        self.notebook.add(self.probe_frame, text="Сетевой зонд Art-Net")

        self.setup_calculator()
        self.setup_probe()

    # ------------------------------------------------------------------ #
    # Menu / diagnostics (hidden from the main screen on purpose - this is
    # for whoever maintains the tool, not for the nightly theatre operator)
    # ------------------------------------------------------------------ #
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        diag_menu = tk.Menu(menubar, tearoff=0)
        diag_menu.add_command(label="Проверить калькулятор (self-test)",
                              command=self._run_calc_selftest)
        diag_menu.add_command(label="Проверить сетевой зонд (self-test)",
                              command=self._run_probe_selftest)
        menubar.add_cascade(label="Диагностика", menu=diag_menu)
        self.root.config(menu=menubar)

    def _run_calc_selftest(self):
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                stage_math.selftest()
            messagebox.showinfo("Self-test калькулятора", "OK\n\n" + buf.getvalue()[-400:])
        except Exception as e:
            messagebox.showerror("Self-test калькулятора провален", str(e))

    def _run_probe_selftest(self):
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                import artnet_probe
                artnet_probe.selftest()
            messagebox.showinfo("Self-test сетевого зонда", "OK\n\n" + buf.getvalue()[-400:])
        except Exception as e:
            messagebox.showerror("Self-test сетевого зонда провален", str(e))

    # ------------------------------------------------------------------ #
    # Calculator tab
    # ------------------------------------------------------------------ #
    def setup_calculator(self):
        lf_stage = ttk.LabelFrame(self.calc_frame, text="Сцена и геометрия")
        lf_stage.pack(fill='x', padx=10, pady=5)

        ttk.Label(lf_stage, text="Ширина (м):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_stage_w = tk.StringVar(value="7.0")
        ttk.Entry(lf_stage, textvariable=self.var_stage_w, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_stage, text="Глубина (м):").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_stage_d = tk.StringVar(value="6.0")
        ttk.Entry(lf_stage, textvariable=self.var_stage_d, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(lf_stage, text="Высота ферм (м):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_truss_h = tk.StringVar(value="4.5")
        ttk.Entry(lf_stage, textvariable=self.var_truss_h, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(lf_stage, text="Отступ камер (м):").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.var_overhang = tk.StringVar(value="0.5")
        ttk.Entry(lf_stage, textvariable=self.var_overhang, width=10).grid(row=1, column=3, padx=5, pady=5)

        lf_cap = ttk.LabelFrame(self.calc_frame, text="Захват движений (Markerless AI)")
        lf_cap.pack(fill='x', padx=10, pady=5)

        ttk.Label(lf_cap, text="Танцовщиков:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_perf = tk.StringVar(value="4")
        ttk.Entry(lf_cap, textvariable=self.var_perf, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_cap, text="Камер:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_cam = tk.StringVar(value="6")
        ttk.Entry(lf_cap, textvariable=self.var_cam, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(lf_cap, text="Сенсор:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        sensor_list = list(stage_math.SENSORS.keys())
        self.var_sensor = tk.StringVar(value="imx392" if "imx392" in sensor_list else sensor_list[0])
        ttk.Combobox(lf_cap, textvariable=self.var_sensor, values=sensor_list, width=15,
                    state="readonly").grid(row=1, column=1, columnspan=3, sticky='w', padx=5, pady=5)

        ttk.Label(lf_cap, text="Кадров/с (FPS):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.var_fps = tk.StringVar(value="60")
        ttk.Entry(lf_cap, textvariable=self.var_fps, width=10).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(lf_cap, text="Светосила (f/):").grid(row=2, column=2, padx=5, pady=5, sticky='w')
        self.var_aperture = tk.StringVar(value="1.4")
        ttk.Entry(lf_cap, textvariable=self.var_aperture, width=10).grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(lf_cap, text="ISO (усиление):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.var_iso = tk.StringVar(value="800")
        ttk.Entry(lf_cap, textvariable=self.var_iso, width=10).grid(row=3, column=1, padx=5, pady=5)

        lf_proj = ttk.LabelFrame(self.calc_frame, text="Проекция на сцене")
        lf_proj.pack(fill='x', padx=10, pady=5)

        ttk.Label(lf_proj, text="Ширина экрана (м):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_scr_w = tk.StringVar(value="7.0")
        ttk.Entry(lf_proj, textvariable=self.var_scr_w, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_proj, text="Высота экрана (м):").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_scr_h = tk.StringVar(value="4.0")
        ttk.Entry(lf_proj, textvariable=self.var_scr_h, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(lf_proj, text="Проекторов:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_proj = tk.StringVar(value="2")
        ttk.Entry(lf_proj, textvariable=self.var_proj, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(lf_proj, text="Люмен (каждый):").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.var_lumens = tk.StringVar(value="10000")
        ttk.Entry(lf_proj, textvariable=self.var_lumens, width=10).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(lf_proj, text="Поверхность:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.var_surf = tk.StringVar(value="Металлизированная сетка (Gain 0.15)")
        ttk.Combobox(lf_proj, textvariable=self.var_surf,
                     values=["Металлизированная сетка (Gain 0.15)", "Белый матовый (Gain 1.0)"],
                     width=35, state="readonly").grid(row=2, column=1, columnspan=3, sticky='w', padx=5, pady=5)

        ttk.Label(lf_proj, text="Перекрытие сшивки (%):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.var_overlap = tk.StringVar(value="15")
        ttk.Entry(lf_proj, textvariable=self.var_overlap, width=10).grid(row=3, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(self.calc_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(btn_frame, text="Рассчитать спецификацию", command=self.calculate).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Экспорт отчёта", command=self.save_report).pack(side='left', padx=5)

        lf_res = ttk.LabelFrame(self.calc_frame, text="ВЕРДИКТ ИНЖЕНЕРНОГО ЯДРА")
        lf_res.pack(fill='both', expand=True, padx=10, pady=5)
        self.text_res = tk.Text(lf_res, height=14, font=('Consolas', 10), state='disabled', bg="#f4f4f4")
        self.text_res.pack(fill='both', expand=True, padx=5, pady=5)
        self._last_report = None

    def log_res(self, message):
        self.text_res.config(state='normal')
        self.text_res.insert(tk.END, message)
        self.text_res.config(state='disabled')

    def calculate(self):
        self.text_res.config(state='normal')
        self.text_res.delete('1.0', tk.END)
        self.text_res.config(state='disabled')

        # Parse and range-check the numeric fields ourselves first, so a typo
        # produces one clear message instead of a generic crash dialog.
        try:
            width = float(self.var_stage_w.get())
            depth = float(self.var_stage_d.get())
            rig_height = float(self.var_truss_h.get())
            inset = float(self.var_overhang.get())
            performers = int(self.var_perf.get())
            cameras = int(self.var_cam.get())
            fps = int(self.var_fps.get())
            f_number = float(self.var_aperture.get())
            iso = float(self.var_iso.get())
            screen_width = float(self.var_scr_w.get())
            screen_height = float(self.var_scr_h.get())
            projectors = int(self.var_proj.get())
            projector_lumens = float(self.var_lumens.get())
            overlap_pct = float(self.var_overlap.get())
        except ValueError:
            messagebox.showerror(
                "Ошибка ввода",
                "Убедитесь, что во всех полях введены числа, а дробные значения "
                "используют точку (например, 7.5).")
            return

        class MockArgs:
            pass

        args = MockArgs()
        args.width = width
        args.depth = depth
        args.rig_height = rig_height
        args.inset = inset
        args.performers = performers
        args.cameras = cameras
        args.preset = self.var_sensor.get()
        args.fps = fps
        args.f_number = f_number
        args.iso = iso
        args.screen_width = screen_width
        args.screen_height = screen_height
        args.projectors = projectors
        args.projector_lumens = projector_lumens
        args.blend_overlap = overlap_pct / 100.0
        args.bit_depth = 8
        args.compressed = False
        args.compression_ratio = 20.0
        args.coverage_margin = 1.1
        args.inference_ms = 100.0
        args.render_fps = 60
        args.screen_gain = 0.15 if "сетка" in self.var_surf.get().lower() else 1.0

        try:
            report = stage_math.analyse(args)
        except stage_math.ValidationError as err:
            # Friendly, specific: this is a checked input problem, not a crash.
            messagebox.showerror("Проверьте значения", str(err))
            return
        except Exception as err:
            messagebox.showerror("Системная ошибка", f"Произошла ошибка в ядре вычислений:\n{err}")
            return

        self._last_report = report
        self._render_report(report)

    def _render_report(self, report):
        inp = report["input"]
        g = report["geometry"]
        e = report["exposure"]
        n = report["network"]
        p = report["projection"]
        l = report["latency"]

        output = (
            f"=== БАЗОВЫЕ ПАРАМЕТРЫ УСТАНОВКИ ===\n"
            f"Сцена: {inp['volume_m']} м | Исполнителей: {inp['performers']} | Камер: {inp['cameras_planned']}\n"
            f"Сенсор: {inp['sensor']} (GS: {'Да' if inp['global_shutter'] else 'Нет - риск ШИМ'})\n\n"
            f"--- 1. ОПТИКА И AI ТРЕКИНГ ---\n"
            f"• Рекомендуемый объектив: {g['recommended_focal_mm']} мм (FOV: {g['actual_horizontal_fov_deg']}° x {g['actual_vertical_fov_deg']}°)\n"
            f"• Фигура танцовщика (в дальнем углу): {g['person_px_far']} px\n"
            f"• Вердикт трекинга: {report['geometry_verdict'].upper()}\n\n"
            f"--- 2. ЭКСПОЗИЦИЯ И ДВИЖЕНИЕ ---\n"
            f"• Макс. выдержка для резких рук: {e['max_exposure_ms']} мс\n"
            f"• Требуемый свет (при f/{e['f_number']}, ISO {e['sensor_iso_equivalent']}): {e['required_scene_illuminance_lux']} lux\n"
            f"• Вердикт света: {e['verdict']}\n\n"
            f"--- 3. СЕТЬ ---\n"
            f"• Поток с 1 камеры: {n['per_camera_gbps']} Гбит/с\n"
            f"• Вердикт Uplink сервера: {n['server_uplink_verdict']}\n\n"
            f"--- 4. ПРОЕКЦИЯ АВАТАРОВ ---\n"
            f"• Эффективный световой поток: {p['effective_lumens']} lm\n"
            f"• Освещенность на поверхности: {p['screen_illuminance_lux']} lux\n"
            f"• Вердикт по яркости: {p['verdict']}\n\n"
            f"--- 5. ОБЩАЯ ЗАДЕРЖКА (End-to-End Latency) ---\n"
            f"• (Camera -> AI -> Unreal Engine -> Projector)\n"
            f"• Оценка: {l['total_ms']} мс - {l['verdict']}\n"
        )
        self.log_res(output)

    def save_report(self):
        text = self.text_res.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Отчёт пуст", "Сначала нажмите «Рассчитать спецификацию».")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Текстовые файлы", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=== ИНЖЕНЕРНЫЙ ОТЧЁТ: СИСТЕМА ЗАХВАТА И ПРОЕКЦИИ ===\n")
                f.write(f"Дата создания: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            messagebox.showinfo("Успешно", "Отчёт сохранён!")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить: {e}")

        if self._last_report is not None:
            json_path = filepath.rsplit(".", 1)[0] + ".json"
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(self._last_report, f, indent=2, ensure_ascii=False)
            except Exception:
                pass  # the .txt report already saved; the .json is a bonus, not critical

    # ------------------------------------------------------------------ #
    # Network probe tab - wired to the real Art-Net QA engine
    # ------------------------------------------------------------------ #
    def setup_probe(self):
        lf_probe = ttk.LabelFrame(self.probe_frame, text="Настройки зонда")
        lf_probe.pack(fill='x', padx=10, pady=10)

        ttk.Label(lf_probe, text="IP-адрес (интерфейс):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_ip = tk.StringVar(value="0.0.0.0")
        ttk.Entry(lf_probe, textvariable=self.var_ip).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_probe, text="Порт (Art-Net = 6454):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_port = tk.StringVar(value=str(ARTNET_PORT))
        ttk.Entry(lf_probe, textvariable=self.var_port).grid(row=1, column=1, padx=5, pady=5)

        self.btn_probe = ttk.Button(lf_probe, text="Запустить зонд", command=self.toggle_probe)
        self.btn_probe.grid(row=2, column=0, columnspan=2, pady=10)

        self.lbl_status = ttk.Label(lf_probe, text="Статус: остановлен", font=('Segoe UI', 10, 'bold'))
        self.lbl_status.grid(row=3, column=0, columnspan=2, pady=(0, 5))

        lf_logs = ttk.LabelFrame(self.probe_frame, text="Состояние сети (обновляется каждую секунду)")
        lf_logs.pack(fill='both', expand=True, padx=10, pady=5)
        self.text_probe = tk.Text(lf_logs, height=15, font=('Consolas', 10), state='disabled')
        self.text_probe.pack(fill='both', expand=True, padx=5, pady=5)
        self.text_probe.tag_configure("ok", foreground="#1a7f37")
        self.text_probe.tag_configure("warn", foreground="#9a6700")
        self.text_probe.tag_configure("bad", foreground="#c62828")

        self.probe = None
        self.probe_running = False
        self.probe_thread = None
        self._probe_refresh_loop()

    def log_probe(self, message, tag=None):
        self.text_probe.config(state='normal')
        stamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.text_probe.insert(tk.END, f"[{stamp}] {message}\n", tag)
        self.text_probe.see(tk.END)
        self.text_probe.config(state='disabled')

    def _set_probe_display(self, text):
        self.text_probe.config(state='normal')
        self.text_probe.delete('1.0', tk.END)
        self.text_probe.insert(tk.END, text)
        self.text_probe.config(state='disabled')

    def toggle_probe(self):
        if not self.probe_running:
            ip = self.var_ip.get()
            try:
                port = int(self.var_port.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Порт должен быть числом!")
                return

            self.probe = ArtNetProbe(bind_addr=ip, port=port)
            try:
                self.probe.start()
            except Exception as e:
                messagebox.showerror("Ошибка сети", f"Не удалось привязать порт: {e}")
                self.probe = None
                return

            self.probe_running = True
            self.btn_probe.config(text="Остановить зонд")
            self.lbl_status.config(text="Статус: слушаем сеть...")
            self.log_probe(f"Слушаем Art-Net на {ip}:{port}. Ждём трафик...")
            # run() blocks until stop() is called or the duration elapses;
            # a generous duration plus an explicit stop() keeps this a clean
            # start/stop toggle without reimplementing the receive loop.
            self.probe_thread = threading.Thread(
                target=self.probe.run, kwargs={"seconds": 24 * 3600}, daemon=True)
            self.probe_thread.start()
        else:
            self.probe_running = False
            if self.probe is not None:
                self.probe.stop()
            self.btn_probe.config(text="Запустить зонд")
            self.lbl_status.config(text="Статус: остановлен")
            self._render_probe_summary(final=True)
            if self.probe is not None:
                self.probe.close()
            self.probe = None

    def _probe_refresh_loop(self):
        if self.probe_running and self.probe is not None:
            self._render_probe_summary(final=False)
        self.root.after(1000, self._probe_refresh_loop)

    def _render_probe_summary(self, final: bool):
        report = self.probe.report()
        rows = report["universes"]
        if not rows:
            self._set_probe_display(
                "Трафик Art-Net не обнаружен.\n"
                "Проверьте VLAN, брандмауэр на UDP 6454 и адрес назначения отправителя.")
            return

        lines = []
        worst_p99 = 0.0
        total_dropped = 0
        total_resets = 0
        for row in rows:
            lines.append(
                f"Universe {row['universe']:>3}  |  {row['packets']:>5} пакетов  |  "
                f"{row['hz']:>5.1f} Гц  |  потери: {row['dropped']:>3}  "
                f"дубли: {row['duplicates']:>2}  перезапуски: {row.get('resets', 0):>2}  |  "
                f"джиттер p99: {row.get('interval_p99_ms', 0):>5.2f} мс"
            )
            worst_p99 = max(worst_p99, row.get("interval_p99_ms", 0.0))
            total_dropped += row["dropped"]
            total_resets += row.get("resets", 0)

        nominal_ms = 1000.0 / 44.0
        if total_dropped or worst_p99 > nominal_ms * 1.5:
            verdict = "ПЛОХО - сеть не готова к показу (потери или джиттер выше одного кадра DMX)"
            tag = "bad"
        elif total_resets:
            verdict = "ХОРОШО, но были перезапуски источника (см. ниже) - не влияет на вердикт"
            tag = "warn"
        else:
            verdict = "ХОРОШО - потерь и джиттера в пределах нормы"
            tag = "ok"

        header = "Финальный отчёт:\n" if final else "Текущее состояние (обновляется):\n"
        body = header + "\n".join(lines) + f"\n\nВЕРДИКТ: {verdict}"
        if total_resets:
            body += (f"\n\nПерезапуски источника обнаружены: {total_resets}. Это не потеря "
                     f"кадров - счётчик источника (например, пульта) просто начался заново "
                     f"после перезагрузки. В вердикт не засчитывается.")
        if report["non_artdmx_packets"]:
            body += f"\n\nНе-Art-Net пакетов на этом порту: {report['non_artdmx_packets']}"

        self._set_probe_display("")
        self.text_probe.config(state='normal')
        self.text_probe.insert(tk.END, body, tag)
        self.text_probe.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = StageRigApp(root)
    root.mainloop()

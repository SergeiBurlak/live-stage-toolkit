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

Interface language defaults to English (this project is US-based and grant
reviewers may open it without notice) with a live switch to Russian from the
Language menu, and room to add more languages - see i18n.py. Only the
interface chrome is translated; the engineering verdicts returned by
stage_math.analyse() (e.g. "LIGHT DEFICIT - add infrared illumination or
faster glass") are fixed English strings from the shared calculation engine
and are not run through the translator, so they read identically regardless
of interface language.

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
from i18n import Translator, LANGUAGES


class StageRigApp:
    def __init__(self, root):
        self.root = root
        self.i18n = Translator()  # defaults to English; see i18n.py
        self._translatable: list = []

        self.root.title(self.i18n("app_title"))
        self.root.geometry("640x600")
        self.root.minsize(560, 420)
        self.root.resizable(True, True)

        self._build_menu()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.calc_frame = ttk.Frame(self.notebook)
        self.probe_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.calc_frame, text=self.i18n("tab_calculator"))
        self.notebook.add(self.probe_frame, text=self.i18n("tab_probe"))

        self.setup_calculator()
        self.setup_probe()

    # ------------------------------------------------------------------ #
    # i18n plumbing
    # ------------------------------------------------------------------ #
    def _label(self, parent, key, **grid_kwargs):
        lbl = ttk.Label(parent, text=self.i18n(key))
        lbl.grid(**grid_kwargs)
        self._translatable.append((lbl, key))
        return lbl

    def _labelframe(self, parent, key, **pack_kwargs):
        frame = ttk.LabelFrame(parent, text=self.i18n(key))
        frame.pack(**pack_kwargs)
        self._translatable.append((frame, key))
        return frame

    def _button(self, parent, key, command, **pack_kwargs):
        btn = ttk.Button(parent, text=self.i18n(key), command=command)
        btn.pack(**pack_kwargs)
        self._translatable.append((btn, key))
        return btn

    def _on_language_selected(self, code: str) -> None:
        self.i18n.set_language(code)
        self._retranslate_all()

    def _retranslate_all(self) -> None:
        for widget, key in self._translatable:
            widget.config(text=self.i18n(key))
        self.root.title(self.i18n("app_title"))
        self.notebook.tab(0, text=self.i18n("tab_calculator"))
        self.notebook.tab(1, text=self.i18n("tab_probe"))
        self._retranslate_menu()
        self._refresh_surface_combo()

        # Widgets whose text depends on runtime state, not a fixed key:
        self.lbl_status.config(
            text=self.i18n("probe_status_listening" if self.probe_running else "probe_status_stopped"))
        self.btn_probe.config(
            text=self.i18n("probe_stop" if self.probe_running else "probe_start"))

        # Re-render whatever is currently on screen so it doesn't stay in
        # the old language until the next calculation / probe tick.
        if self._last_report is not None:
            self._render_report(self._last_report)
        if self.probe is not None:
            self._render_probe_summary(final=not self.probe_running)

    # ------------------------------------------------------------------ #
    # Menu (Diagnostics + Language)
    # ------------------------------------------------------------------ #
    def _build_menu(self):
        self.menubar = tk.Menu(self.root)

        self.diag_menu = tk.Menu(self.menubar, tearoff=0)
        self.diag_menu.add_command(label=self.i18n("menu_diag_calc"), command=self._run_calc_selftest)
        self.diag_menu.add_command(label=self.i18n("menu_diag_probe"), command=self._run_probe_selftest)
        self.menubar.add_cascade(label=self.i18n("menu_diagnostics"), menu=self.diag_menu)

        # Language names are shown in their own language (e.g. "Русский" is
        # never translated), so this menu itself needs no i18n lookup for
        # its entries - only its own cascade label is translated.
        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self._lang_var = tk.StringVar(value=self.i18n.language)
        for code, display_name in LANGUAGES.items():
            self.lang_menu.add_radiobutton(
                label=display_name, value=code, variable=self._lang_var,
                command=lambda c=code: self._on_language_selected(c))
        self.menubar.add_cascade(label=self.i18n("menu_language"), menu=self.lang_menu)

        self.root.config(menu=self.menubar)

    def _retranslate_menu(self):
        # Indices match the add_cascade() order in _build_menu() above.
        self.menubar.entryconfig(0, label=self.i18n("menu_diagnostics"))
        self.diag_menu.entryconfig(0, label=self.i18n("menu_diag_calc"))
        self.diag_menu.entryconfig(1, label=self.i18n("menu_diag_probe"))
        self.menubar.entryconfig(1, label=self.i18n("menu_language"))

    def _run_calc_selftest(self):
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                stage_math.selftest()
            messagebox.showinfo(self.i18n("selftest_calc_title"), "OK\n\n" + buf.getvalue()[-400:])
        except Exception as e:
            messagebox.showerror(self.i18n("selftest_calc_fail_title"), str(e))

    def _run_probe_selftest(self):
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                import artnet_probe
                artnet_probe.selftest()
            messagebox.showinfo(self.i18n("selftest_probe_title"), "OK\n\n" + buf.getvalue()[-400:])
        except Exception as e:
            messagebox.showerror(self.i18n("selftest_probe_fail_title"), str(e))

    # ------------------------------------------------------------------ #
    # Calculator tab
    # ------------------------------------------------------------------ #
    def setup_calculator(self):
        lf_stage = self._labelframe(self.calc_frame, "frame_stage", fill='x', padx=10, pady=5)

        self._label(lf_stage, "field_width", row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_stage_w = tk.StringVar(value="7.0")
        ttk.Entry(lf_stage, textvariable=self.var_stage_w, width=10).grid(row=0, column=1, padx=5, pady=5)

        self._label(lf_stage, "field_depth", row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_stage_d = tk.StringVar(value="6.0")
        ttk.Entry(lf_stage, textvariable=self.var_stage_d, width=10).grid(row=0, column=3, padx=5, pady=5)

        self._label(lf_stage, "field_rig_height", row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_truss_h = tk.StringVar(value="4.5")
        ttk.Entry(lf_stage, textvariable=self.var_truss_h, width=10).grid(row=1, column=1, padx=5, pady=5)

        self._label(lf_stage, "field_inset", row=1, column=2, padx=5, pady=5, sticky='w')
        self.var_overhang = tk.StringVar(value="0.5")
        ttk.Entry(lf_stage, textvariable=self.var_overhang, width=10).grid(row=1, column=3, padx=5, pady=5)

        lf_cap = self._labelframe(self.calc_frame, "frame_capture", fill='x', padx=10, pady=5)

        self._label(lf_cap, "field_performers", row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_perf = tk.StringVar(value="4")
        ttk.Entry(lf_cap, textvariable=self.var_perf, width=10).grid(row=0, column=1, padx=5, pady=5)

        self._label(lf_cap, "field_cameras", row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_cam = tk.StringVar(value="6")
        ttk.Entry(lf_cap, textvariable=self.var_cam, width=10).grid(row=0, column=3, padx=5, pady=5)

        # Sensor codes ("imx392", etc.) are technical identifiers shared with
        # stage_math.SENSORS - they are not language-dependent and are not
        # translated.
        self._label(lf_cap, "field_sensor", row=1, column=0, padx=5, pady=5, sticky='w')
        sensor_list = list(stage_math.SENSORS.keys())
        self.var_sensor = tk.StringVar(value="imx392" if "imx392" in sensor_list else sensor_list[0])
        ttk.Combobox(lf_cap, textvariable=self.var_sensor, values=sensor_list, width=15,
                    state="readonly").grid(row=1, column=1, columnspan=3, sticky='w', padx=5, pady=5)

        self._label(lf_cap, "field_fps", row=2, column=0, padx=5, pady=5, sticky='w')
        self.var_fps = tk.StringVar(value="60")
        ttk.Entry(lf_cap, textvariable=self.var_fps, width=10).grid(row=2, column=1, padx=5, pady=5)

        self._label(lf_cap, "field_aperture", row=2, column=2, padx=5, pady=5, sticky='w')
        self.var_aperture = tk.StringVar(value="1.4")
        ttk.Entry(lf_cap, textvariable=self.var_aperture, width=10).grid(row=2, column=3, padx=5, pady=5)

        self._label(lf_cap, "field_iso", row=3, column=0, padx=5, pady=5, sticky='w')
        self.var_iso = tk.StringVar(value="800")
        ttk.Entry(lf_cap, textvariable=self.var_iso, width=10).grid(row=3, column=1, padx=5, pady=5)

        lf_proj = self._labelframe(self.calc_frame, "frame_projection", fill='x', padx=10, pady=5)

        self._label(lf_proj, "field_screen_width", row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_scr_w = tk.StringVar(value="7.0")
        ttk.Entry(lf_proj, textvariable=self.var_scr_w, width=10).grid(row=0, column=1, padx=5, pady=5)

        self._label(lf_proj, "field_screen_height", row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_scr_h = tk.StringVar(value="4.0")
        ttk.Entry(lf_proj, textvariable=self.var_scr_h, width=10).grid(row=0, column=3, padx=5, pady=5)

        self._label(lf_proj, "field_projectors", row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_proj = tk.StringVar(value="2")
        ttk.Entry(lf_proj, textvariable=self.var_proj, width=10).grid(row=1, column=1, padx=5, pady=5)

        self._label(lf_proj, "field_lumens", row=1, column=2, padx=5, pady=5, sticky='w')
        self.var_lumens = tk.StringVar(value="10000")
        ttk.Entry(lf_proj, textvariable=self.var_lumens, width=10).grid(row=1, column=3, padx=5, pady=5)

        # Surface choice: the underlying value used by the calculation
        # (screen_gain) is driven by an internal code ("scrim"/"matte"),
        # never by pattern-matching the localized display text - that was
        # a real bug risk (matching Russian "сетка" would silently break
        # once the label read "scrim" in English).
        self._label(lf_proj, "field_surface", row=2, column=0, padx=5, pady=5, sticky='w')
        self._surface_codes = ["scrim", "matte"]
        self.var_surface_code = tk.StringVar(value="scrim")
        self.var_surf_display = tk.StringVar()
        self.cmb_surface = ttk.Combobox(lf_proj, textvariable=self.var_surf_display,
                                        width=35, state="readonly")
        self.cmb_surface.grid(row=2, column=1, columnspan=3, sticky='w', padx=5, pady=5)
        self.cmb_surface.bind("<<ComboboxSelected>>", self._on_surface_selected)
        self._refresh_surface_combo()

        self._label(lf_proj, "field_overlap", row=3, column=0, padx=5, pady=5, sticky='w')
        self.var_overlap = tk.StringVar(value="15")
        ttk.Entry(lf_proj, textvariable=self.var_overlap, width=10).grid(row=3, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(self.calc_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        self._button(btn_frame, "btn_calculate", self.calculate, side='left', padx=5)
        self._button(btn_frame, "btn_export", self.save_report, side='left', padx=5)

        lf_res = self._labelframe(self.calc_frame, "frame_verdict", fill='both', expand=True, padx=10, pady=5)
        self.text_res = tk.Text(lf_res, height=8, font=('Consolas', 10), state='disabled', bg="#f4f4f4")
        self.text_res.pack(fill='both', expand=True, padx=5, pady=5)
        self._last_report = None

    def _refresh_surface_combo(self):
        values = [self.i18n(f"surface_{code}") for code in self._surface_codes]
        self.cmb_surface["values"] = values
        idx = self._surface_codes.index(self.var_surface_code.get())
        self.var_surf_display.set(values[idx])

    def _on_surface_selected(self, event=None):
        idx = self.cmb_surface.current()
        if idx >= 0:
            self.var_surface_code.set(self._surface_codes[idx])

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
            messagebox.showerror(self.i18n("err_input_title"), self.i18n("err_input_body"))
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
        args.screen_gain = 0.15 if self.var_surface_code.get() == "scrim" else 1.0

        try:
            report = stage_math.analyse(args)
        except stage_math.ValidationError as err:
            # Friendly, specific: this is a checked input problem, not a crash.
            messagebox.showerror(self.i18n("err_validation_title"), str(err))
            return
        except Exception as err:
            messagebox.showerror(self.i18n("err_system_title"), self.i18n("err_system_body", err=err))
            return

        self._last_report = report
        self._render_report(report)

    def _render_report(self, report):
        # NOTE: verdict/sensor-note strings inside `report` come straight
        # from stage_math.analyse() and are fixed English - intentionally
        # not translated, see the module docstring.
        t = self.i18n
        inp = report["input"]
        g = report["geometry"]
        e = report["exposure"]
        n = report["network"]
        p = report["projection"]
        l = report["latency"]

        lines = [
            t("report_header"),
            t("report_scene_line", volume=inp['volume_m'], performers=inp['performers'],
              cameras=inp['cameras_planned']),
            t("report_sensor_line", sensor=inp['sensor'], gs=t("yes") if inp['global_shutter'] else t("no")),
            "",
            t("report_section_1"),
            t("report_lens", focal=g['recommended_focal_mm'],
              h_fov=g['actual_horizontal_fov_deg'], v_fov=g['actual_vertical_fov_deg']),
            t("report_person_px", px=g['person_px_far']),
            t("report_tracking_verdict", verdict=report['geometry_verdict'].upper()),
            "",
            t("report_section_2"),
            t("report_max_exposure", ms=e['max_exposure_ms']),
            t("report_required_light", f_number=e['f_number'], iso=e['sensor_iso_equivalent'],
              lux=e['required_scene_illuminance_lux']),
            t("report_light_verdict", verdict=e['verdict']),
            "",
            t("report_section_3"),
            t("report_per_camera", gbps=n['per_camera_gbps']),
            t("report_uplink_verdict", verdict=n['server_uplink_verdict']),
            "",
            t("report_section_4"),
            t("report_effective_lumens", lumens=p['effective_lumens']),
            t("report_screen_illuminance", lux=p['screen_illuminance_lux']),
            t("report_brightness_verdict", verdict=p['verdict']),
            "",
            t("report_section_5"),
            t("report_latency_path"),
            t("report_latency_estimate", ms=l['total_ms'], verdict=l['verdict']),
        ]
        self.text_res.config(state='normal')
        self.text_res.delete('1.0', tk.END)
        self.text_res.insert(tk.END, "\n".join(lines) + "\n")
        self.text_res.config(state='disabled')

    def save_report(self):
        text = self.text_res.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning(self.i18n("report_empty_title"), self.i18n("report_empty_body"))
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{self.i18n('frame_verdict')}\n")
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            messagebox.showinfo(self.i18n("save_ok_title"), self.i18n("save_ok_body"))
        except Exception as e:
            messagebox.showerror(self.i18n("save_err_title"), self.i18n("save_err_body", err=e))

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
        lf_probe = self._labelframe(self.probe_frame, "probe_settings", fill='x', padx=10, pady=10)

        self._label(lf_probe, "probe_ip_label", row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_ip = tk.StringVar(value="0.0.0.0")
        ttk.Entry(lf_probe, textvariable=self.var_ip).grid(row=0, column=1, padx=5, pady=5)

        self._label(lf_probe, "probe_port_label", row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_port = tk.StringVar(value=str(ARTNET_PORT))
        ttk.Entry(lf_probe, textvariable=self.var_port).grid(row=1, column=1, padx=5, pady=5)

        self.btn_probe = ttk.Button(lf_probe, text=self.i18n("probe_start"), command=self.toggle_probe)
        self.btn_probe.grid(row=2, column=0, columnspan=2, pady=10)

        self.lbl_status = ttk.Label(lf_probe, text=self.i18n("probe_status_stopped"),
                                    font=('Segoe UI', 10, 'bold'))
        self.lbl_status.grid(row=3, column=0, columnspan=2, pady=(0, 5))

        lf_logs = self._labelframe(self.probe_frame, "probe_log_frame", fill='both', expand=True, padx=10, pady=5)
        self.text_probe = tk.Text(lf_logs, height=8, font=('Consolas', 10), state='disabled')
        self.text_probe.pack(fill='both', expand=True, padx=5, pady=5)
        self.text_probe.tag_configure("ok", foreground="#1a7f37")
        self.text_probe.tag_configure("warn", foreground="#9a6700")
        self.text_probe.tag_configure("bad", foreground="#c62828")

        self.probe = None
        self.probe_running = False
        self.probe_thread = None
        self._probe_refresh_loop()

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
                messagebox.showerror(self.i18n("probe_port_error_title"), self.i18n("probe_port_error_body"))
                return

            self.probe = ArtNetProbe(bind_addr=ip, port=port)
            try:
                self.probe.start()
            except Exception as e:
                messagebox.showerror(self.i18n("probe_bind_error_title"),
                                     self.i18n("probe_bind_error_body", err=e))
                self.probe = None
                return

            self.probe_running = True
            self.btn_probe.config(text=self.i18n("probe_stop"))
            self.lbl_status.config(text=self.i18n("probe_status_listening"))
            self._set_probe_display(self.i18n("probe_listening", ip=ip, port=port))
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
            self.btn_probe.config(text=self.i18n("probe_start"))
            self.lbl_status.config(text=self.i18n("probe_status_stopped"))
            self._render_probe_summary(final=True)
            if self.probe is not None:
                self.probe.close()
            self.probe = None

    def _probe_refresh_loop(self):
        if self.probe_running and self.probe is not None:
            self._render_probe_summary(final=False)
        self.root.after(1000, self._probe_refresh_loop)

    def _render_probe_summary(self, final: bool):
        t = self.i18n
        report = self.probe.report()
        rows = report["universes"]
        if not rows:
            self._set_probe_display(t("probe_no_traffic"))
            return

        lines = []
        worst_p99 = 0.0
        total_dropped = 0
        total_resets = 0
        for row in rows:
            lines.append(t(
                "probe_row",
                universe=row['universe'], packets=row['packets'], hz=row['hz'],
                dropped=row['dropped'], dup=row['duplicates'],
                resets=row.get('resets', 0), p99=row.get('interval_p99_ms', 0),
            ))
            worst_p99 = max(worst_p99, row.get("interval_p99_ms", 0.0))
            total_dropped += row["dropped"]
            total_resets += row.get("resets", 0)

        nominal_ms = 1000.0 / 44.0
        if total_dropped or worst_p99 > nominal_ms * 1.5:
            verdict = t("probe_verdict_bad")
            tag = "bad"
        elif total_resets:
            verdict = t("probe_verdict_warn")
            tag = "warn"
        else:
            verdict = t("probe_verdict_ok")
            tag = "ok"

        header = t("probe_final_header") if final else t("probe_live_header")
        body = header + "\n".join(lines) + "\n\n" + t("probe_verdict_label", verdict=verdict)
        if total_resets:
            body += "\n\n" + t("probe_resets_note", count=total_resets)
        if report["non_artdmx_packets"]:
            body += "\n\n" + t("probe_non_artdmx_note", count=report["non_artdmx_packets"])

        self.text_probe.config(state='normal')
        self.text_probe.delete('1.0', tk.END)
        self.text_probe.insert(tk.END, body, tag)
        self.text_probe.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = StageRigApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import threading
import datetime

# Импортируем вашу оригинальную математику из соседнего файла
import stage_math


class StageRigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Инженерный калькулятор: Захват движений и Проекция")
        self.root.geometry("600x750")
        self.root.resizable(True, True)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.calc_frame = ttk.Frame(self.notebook)
        self.probe_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.calc_frame, text="Калькулятор (Mocap & Проекция)")
        self.notebook.add(self.probe_frame, text="Сетевой UDP зонд")

        self.setup_calculator()
        self.setup_probe()

    def setup_calculator(self):
        # --- БЛОК: Сцена ---
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

        # --- БЛОК: Захват (Трекинг) ---
        lf_cap = ttk.LabelFrame(self.calc_frame, text="Захват движений (Markerless AI)")
        lf_cap.pack(fill='x', padx=10, pady=5)

        ttk.Label(lf_cap, text="Танцовщиков:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_perf = tk.StringVar(value="4")
        ttk.Entry(lf_cap, textvariable=self.var_perf, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_cap, text="Камер:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.var_cam = tk.StringVar(value="6")
        ttk.Entry(lf_cap, textvariable=self.var_cam, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(lf_cap, text="Сенсор:").grid(row=1, column=0, padx=5, pady=5, sticky='w')

        # Динамически загружаем список сенсоров из оригинального движка
        sensor_list = list(stage_math.SENSORS.keys())
        self.var_sensor = tk.StringVar(value="imx392" if "imx392" in sensor_list else sensor_list[0])
        ttk.Combobox(lf_cap, textvariable=self.var_sensor, values=sensor_list, width=15, state="readonly").grid(row=1,
                                                                                                                column=1,
                                                                                                                columnspan=3,
                                                                                                                sticky='w',
                                                                                                                padx=5,
                                                                                                                pady=5)

        ttk.Label(lf_cap, text="Кадров/с (FPS):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.var_fps = tk.StringVar(value="60")
        ttk.Entry(lf_cap, textvariable=self.var_fps, width=10).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(lf_cap, text="Светосила (f/):").grid(row=2, column=2, padx=5, pady=5, sticky='w')
        self.var_aperture = tk.StringVar(value="1.4")
        ttk.Entry(lf_cap, textvariable=self.var_aperture, width=10).grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(lf_cap, text="ISO (усиление):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.var_iso = tk.StringVar(value="800")
        ttk.Entry(lf_cap, textvariable=self.var_iso, width=10).grid(row=3, column=1, padx=5, pady=5)

        # --- БЛОК: Проекция ---
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

        # --- Кнопки ---
        btn_frame = ttk.Frame(self.calc_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(btn_frame, text="Рассчитать спецификацию", command=self.calculate).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Экспорт отчёта", command=self.save_report).pack(side='left', padx=5)

        # --- Результат ---
        lf_res = ttk.LabelFrame(self.calc_frame, text="ВЕРДИКТ ИНЖЕНЕРНОГО ЯДРА")
        lf_res.pack(fill='both', expand=True, padx=10, pady=5)

        self.text_res = tk.Text(lf_res, height=14, font=('Consolas', 10), state='disabled', bg="#f4f4f4")
        self.text_res.pack(fill='both', expand=True, padx=5, pady=5)

    def setup_probe(self):
        # (Сетевой зонд оставлен без изменений, с вашими правками)
        lf_probe = ttk.LabelFrame(self.probe_frame, text="Настройки UDP зонда")
        lf_probe.pack(fill='x', padx=10, pady=10)

        ttk.Label(lf_probe, text="IP-адрес:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.var_ip = tk.StringVar(value="0.0.0.0")
        ttk.Entry(lf_probe, textvariable=self.var_ip).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(lf_probe, text="Порт:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.var_port = tk.StringVar(value="8080")
        ttk.Entry(lf_probe, textvariable=self.var_port).grid(row=1, column=1, padx=5, pady=5)

        self.btn_probe = ttk.Button(lf_probe, text="Запустить зонд", command=self.toggle_probe)
        self.btn_probe.grid(row=2, column=0, columnspan=2, pady=10)

        lf_logs = ttk.LabelFrame(self.probe_frame, text="Сетевой трафик")
        lf_logs.pack(fill='both', expand=True, padx=10, pady=5)
        self.text_probe = tk.Text(lf_logs, height=15, font=('Consolas', 10), state='disabled')
        self.text_probe.pack(fill='both', expand=True, padx=5, pady=5)

        self.probe_running = False
        self.probe_socket = None

    def log_res(self, message):
        self.text_res.config(state='normal')
        self.text_res.insert(tk.END, message)
        self.text_res.config(state='disabled')

    def log_probe(self, message):
        self.text_probe.config(state='normal')
        self.text_probe.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.text_probe.see(tk.END)
        self.text_probe.config(state='disabled')

    def calculate(self):
        self.text_res.config(state='normal')
        self.text_res.delete('1.0', tk.END)

        try:
            # 1. Создаем объект (mock) аргументов для передачи в stage_math
            class MockArgs:
                pass

            args = MockArgs()

            # Заполняем данные из GUI
            args.width = float(self.var_stage_w.get())
            args.depth = float(self.var_stage_d.get())
            args.rig_height = float(self.var_truss_h.get())
            args.inset = float(self.var_overhang.get())
            args.performers = int(self.var_perf.get())
            args.cameras = int(self.var_cam.get())
            args.preset = self.var_sensor.get()
            args.fps = int(self.var_fps.get())
            args.f_number = float(self.var_aperture.get())
            args.iso = float(self.var_iso.get())

            args.screen_width = float(self.var_scr_w.get())
            args.screen_height = float(self.var_scr_h.get())
            args.projectors = int(self.var_proj.get())
            args.projector_lumens = float(self.var_lumens.get())
            args.blend_overlap = float(self.var_overlap.get()) / 100.0

            # Заполняем скрытые/системные параметры, которые нужны движку
            args.bit_depth = 8
            args.compressed = False
            args.compression_ratio = 20.0
            args.coverage_margin = 1.1
            args.inference_ms = 100.0
            args.render_fps = 60

            # Определяем Screen Gain на основе выпадающего списка
            if "сетка" in self.var_surf.get().lower():
                args.screen_gain = 0.15
            else:
                args.screen_gain = 1.0

            # 2. ВЫЗЫВАЕМ ВАШУ ФИЗИЧЕСКУЮ МАТЕМАТИКУ!
            report = stage_math.analyse(args)

            # 3. Красиво форматируем ответ из полученного словаря
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

        except ValueError:
            messagebox.showerror("Ошибка ввода",
                                 "Убедитесь, что во всех полях введены числа, а дробные значения используют точку (например, 7.5).")
        except Exception as err:
            messagebox.showerror("Системная ошибка", f"Произошла ошибка в ядре вычислений:\n{str(err)}")
        finally:
            self.text_res.config(state='disabled')

    def save_report(self):
        text = self.text_res.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Отчёт пуст", "Сначала нажмите «Рассчитать спецификацию».")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("=== ИНЖЕНЕРНЫЙ ОТЧЁТ: СИСТЕМА ЗАХВАТА И ПРОЕКЦИИ ===\n")
                    f.write(f"Дата создания: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(text)
                messagebox.showinfo("Успешно", "Отчёт сохранён!")
            except Exception as e:
                messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить: {e}")

    def toggle_probe(self):
        if not self.probe_running:
            ip = self.var_ip.get()
            try:
                port = int(self.var_port.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Порт должен быть числом!")
                return

            self.probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.probe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.probe_socket.bind((ip, port))
            except Exception as e:
                messagebox.showerror("Ошибка сети", f"Не удалось привязать порт: {e}")
                if self.probe_socket: self.probe_socket.close()
                return

            self.probe_running = True
            self.btn_probe.config(text="Остановить зонд")
            self.log_probe(f"Слушаем {ip}:{port}... (Готово к приему OSC / Tracking data)")
            threading.Thread(target=self.receive_data, daemon=True).start()
        else:
            self.probe_running = False
            if self.probe_socket:
                self.probe_socket.close()
            self.btn_probe.config(text="Запустить зонд")
            self.log_probe("Зонд остановлен.")

    def receive_data(self):
        while self.probe_running:
            try:
                data, addr = self.probe_socket.recvfrom(2048)
                self.root.after(0, self.log_probe, f"Пакет от {addr}: {len(data)} байт")
            except OSError:
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = StageRigApp(root)
    root.mainloop()
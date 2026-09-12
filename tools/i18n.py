"""
i18n.py - minimal, dependency-free internationalization for Live Stage
Toolkit GUIs.

Design goals, in order of priority:
  1. English is the default and the fallback. Anyone who clones the
     repository and runs a tool - a grant reviewer, a contributor who
     doesn't read Russian - sees English immediately, with zero setup.
  2. Adding a language means adding one dict. It does not touch any GUI
     code. A partial translation is safe: any key missing from a language
     falls back to English automatically, so the interface never shows a
     raw key name or crashes over an untranslated string.
  3. No dependencies beyond the standard library, matching the rest of the
     toolkit.

Usage
-----
    from i18n import Translator

    t = Translator()                 # defaults to English
    t.set_language("ru")
    label_text = t("field_width")    # looked up, with fallback to English

    # Formatting: pass keyword arguments, applied with str.format()
    t("probe_listening", ip="0.0.0.0", port=6454)

Adding a language
------------------
Add a new entry to LANGUAGES (code -> display name) and a new dict to
TRANSLATIONS (code -> {key: text}). You do not need to translate every
key on day one - untranslated keys silently show English until someone
fills them in. Keep the same {placeholders} as the English source string
for any key you do translate, or str.format() will raise at render time.

Part of the Live Stage Toolkit. MIT licence.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"

# Display names shown in the language switcher itself - each language names
# itself, not translated through the table below.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "ru": "Русский",
}

# Source of truth. Every key used anywhere in a toolkit GUI must exist here.
# Every other language dict is allowed to be a partial subset of this one.
_EN: dict[str, str] = {
    # --- Window / menu ---
    "app_title": "Engineering Calculator: Motion Capture & Projection",
    "menu_diagnostics": "Diagnostics",
    "menu_diag_calc": "Test calculator (self-test)",
    "menu_diag_probe": "Test network probe (self-test)",
    "menu_language": "Language",

    # --- Tabs ---
    "tab_calculator": "Calculator (Mocap & Projection)",
    "tab_probe": "Art-Net Network Probe",

    # --- Calculator tab: section frames ---
    "frame_stage": "Stage & Geometry",
    "frame_capture": "Motion Capture (Markerless AI)",
    "frame_projection": "Stage Projection",
    "frame_verdict": "ENGINEERING CORE VERDICT",

    # --- Calculator tab: field labels ---
    "field_width": "Width (m):",
    "field_depth": "Depth (m):",
    "field_rig_height": "Truss height (m):",
    "field_inset": "Camera inset (m):",
    "field_performers": "Performers:",
    "field_cameras": "Cameras:",
    "field_sensor": "Sensor:",
    "field_fps": "Frame rate (FPS):",
    "field_aperture": "Aperture (f/):",
    "field_iso": "ISO (gain):",
    "field_screen_width": "Screen width (m):",
    "field_screen_height": "Screen height (m):",
    "field_projectors": "Projectors:",
    "field_lumens": "Lumens (each):",
    "field_surface": "Surface:",
    "field_overlap": "Blend overlap (%):",

    # --- Surface choices (internal codes: "scrim", "matte") ---
    "surface_scrim": "Metallized scrim (Gain 0.15)",
    "surface_matte": "White matte (Gain 1.0)",

    # --- Calculator tab: buttons ---
    "btn_calculate": "Calculate specification",
    "btn_export": "Export report",

    # --- Calculator report template ---
    "report_header": "=== BASELINE INSTALLATION PARAMETERS ===",
    "report_scene_line": "Stage: {volume} m | Performers: {performers} | Cameras: {cameras}",
    "report_sensor_line": "Sensor: {sensor} (Global shutter: {gs})",
    "yes": "Yes",
    "no": "No - PWM banding risk",
    "report_section_1": "--- 1. OPTICS AND AI TRACKING ---",
    "report_lens": "\u2022 Recommended lens: {focal} mm (FOV: {h_fov}\u00b0 x {v_fov}\u00b0)",
    "report_person_px": "\u2022 Performer figure (far corner): {px} px",
    "report_tracking_verdict": "\u2022 Tracking verdict: {verdict}",
    "report_section_2": "--- 2. EXPOSURE AND MOTION ---",
    "report_max_exposure": "\u2022 Max. exposure for sharp hands: {ms} ms",
    "report_required_light": "\u2022 Required light (at f/{f_number}, ISO {iso}): {lux} lux",
    "report_light_verdict": "\u2022 Light verdict: {verdict}",
    "report_section_3": "--- 3. NETWORK ---",
    "report_per_camera": "\u2022 Per-camera stream: {gbps} Gbit/s",
    "report_uplink_verdict": "\u2022 Server uplink verdict: {verdict}",
    "report_section_4": "--- 4. AVATAR PROJECTION ---",
    "report_effective_lumens": "\u2022 Effective luminous flux: {lumens} lm",
    "report_screen_illuminance": "\u2022 Surface illuminance: {lux} lux",
    "report_brightness_verdict": "\u2022 Brightness verdict: {verdict}",
    "report_section_5": "--- 5. END-TO-END LATENCY ---",
    "report_latency_path": "\u2022 (Camera -> AI -> Unreal Engine -> Projector)",
    "report_latency_estimate": "\u2022 Estimate: {ms} ms - {verdict}",

    # --- Calculator: dialogs ---
    "err_input_title": "Input error",
    "err_input_body": ("Please make sure every field contains a number, "
                       "and that decimals use a period (e.g. 7.5)."),
    "err_validation_title": "Check the values",
    "err_system_title": "System error",
    "err_system_body": "An error occurred in the calculation core:\n{err}",
    "report_empty_title": "Report is empty",
    "report_empty_body": "Click \u201cCalculate specification\u201d first.",
    "save_ok_title": "Saved",
    "save_ok_body": "Report saved!",
    "save_ok_body_path": "Report saved to:\n{path}",
    "save_err_title": "Save error",
    "save_err_body": "Could not save: {err}",

    # --- Diagnostics dialogs ---
    "selftest_calc_title": "Calculator self-test",
    "selftest_calc_fail_title": "Calculator self-test failed",
    "selftest_probe_title": "Network probe self-test",
    "selftest_probe_fail_title": "Network probe self-test failed",

    # --- Probe tab ---
    "probe_settings": "Probe settings",
    "probe_ip_label": "IP address (interface):",
    "probe_port_label": "Port (Art-Net = 6454):",
    "probe_start": "Start probe",
    "probe_stop": "Stop probe",
    "probe_status_stopped": "Status: stopped",
    "probe_status_listening": "Status: listening...",
    "probe_log_frame": "Network status (updates every second)",
    "probe_port_error_title": "Error",
    "probe_port_error_body": "Port must be a number!",
    "probe_bind_error_title": "Network error",
    "probe_bind_error_body": "Could not bind the port: {err}",
    "probe_listening": "Listening for Art-Net on {ip}:{port}. Waiting for traffic...",
    "probe_no_traffic": ("No Art-Net traffic detected.\n"
                         "Check the VLAN, the firewall on UDP 6454, and the sender's target address."),
    "probe_final_header": "Final report:\n",
    "probe_live_header": "Current status (updating):\n",
    "probe_verdict_label": "VERDICT: {verdict}",
    "probe_verdict_bad": "BAD - network is not show-ready (loss or jitter above one DMX frame)",
    "probe_verdict_warn": "GOOD, but sender restarts were seen (see below) - does not affect the verdict",
    "probe_verdict_ok": "GOOD - loss and jitter within show tolerance",
    "probe_resets_note": ("Sender restarts detected: {count}. This is not lost frames - the "
                          "source's own counter (e.g. a console) simply started over after a "
                          "reboot. Not counted in the verdict."),
    "probe_non_artdmx_note": "Non-Art-Net packets on this port: {count}",
    "probe_row": ("Universe {universe:>3}  |  {packets:>5} packets  |  {hz:>5.1f} Hz  |  "
                 "loss: {dropped:>3}  dup: {dup:>2}  restarts: {resets:>2}  |  "
                 "p99 jitter: {p99:>5.2f} ms"),
}

# Russian translation. Kept as a full, complete set (this project's working
# language today); future languages can start as a much smaller partial
# dict and still work correctly - see the module docstring.
_RU: dict[str, str] = {
    "app_title": "Инженерный калькулятор: Захват движений и Проекция",
    "menu_diagnostics": "Диагностика",
    "menu_diag_calc": "Проверить калькулятор (self-test)",
    "menu_diag_probe": "Проверить сетевой зонд (self-test)",
    "menu_language": "Язык",

    "tab_calculator": "Калькулятор (Mocap & Проекция)",
    "tab_probe": "Сетевой зонд Art-Net",

    "frame_stage": "Сцена и геометрия",
    "frame_capture": "Захват движений (Markerless AI)",
    "frame_projection": "Проекция на сцене",
    "frame_verdict": "ВЕРДИКТ ИНЖЕНЕРНОГО ЯДРА",

    "field_width": "Ширина (м):",
    "field_depth": "Глубина (м):",
    "field_rig_height": "Высота ферм (м):",
    "field_inset": "Отступ камер (м):",
    "field_performers": "Танцовщиков:",
    "field_cameras": "Камер:",
    "field_sensor": "Сенсор:",
    "field_fps": "Кадров/с (FPS):",
    "field_aperture": "Светосила (f/):",
    "field_iso": "ISO (усиление):",
    "field_screen_width": "Ширина экрана (м):",
    "field_screen_height": "Высота экрана (м):",
    "field_projectors": "Проекторов:",
    "field_lumens": "Люмен (каждый):",
    "field_surface": "Поверхность:",
    "field_overlap": "Перекрытие сшивки (%):",

    "surface_scrim": "Металлизированная сетка (Gain 0.15)",
    "surface_matte": "Белый матовый (Gain 1.0)",

    "btn_calculate": "Рассчитать спецификацию",
    "btn_export": "Экспорт отчёта",

    "report_header": "=== БАЗОВЫЕ ПАРАМЕТРЫ УСТАНОВКИ ===",
    "report_scene_line": "Сцена: {volume} м | Исполнителей: {performers} | Камер: {cameras}",
    "report_sensor_line": "Сенсор: {sensor} (Глобальный затвор: {gs})",
    "yes": "Да",
    "no": "Нет - риск ШИМ",
    "report_section_1": "--- 1. ОПТИКА И AI ТРЕКИНГ ---",
    "report_lens": "\u2022 Рекомендуемый объектив: {focal} мм (FOV: {h_fov}\u00b0 x {v_fov}\u00b0)",
    "report_person_px": "\u2022 Фигура танцовщика (в дальнем углу): {px} px",
    "report_tracking_verdict": "\u2022 Вердикт трекинга: {verdict}",
    "report_section_2": "--- 2. ЭКСПОЗИЦИЯ И ДВИЖЕНИЕ ---",
    "report_max_exposure": "\u2022 Макс. выдержка для резких рук: {ms} мс",
    "report_required_light": "\u2022 Требуемый свет (при f/{f_number}, ISO {iso}): {lux} lux",
    "report_light_verdict": "\u2022 Вердикт света: {verdict}",
    "report_section_3": "--- 3. СЕТЬ ---",
    "report_per_camera": "\u2022 Поток с 1 камеры: {gbps} Гбит/с",
    "report_uplink_verdict": "\u2022 Вердикт Uplink сервера: {verdict}",
    "report_section_4": "--- 4. ПРОЕКЦИЯ АВАТАРОВ ---",
    "report_effective_lumens": "\u2022 Эффективный световой поток: {lumens} lm",
    "report_screen_illuminance": "\u2022 Освещённость на поверхности: {lux} lux",
    "report_brightness_verdict": "\u2022 Вердикт по яркости: {verdict}",
    "report_section_5": "--- 5. ОБЩАЯ ЗАДЕРЖКА (End-to-End Latency) ---",
    "report_latency_path": "\u2022 (Camera -> AI -> Unreal Engine -> Projector)",
    "report_latency_estimate": "\u2022 Оценка: {ms} мс - {verdict}",

    "err_input_title": "Ошибка ввода",
    "err_input_body": ("Убедитесь, что во всех полях введены числа, а дробные значения "
                       "используют точку (например, 7.5)."),
    "err_validation_title": "Проверьте значения",
    "err_system_title": "Системная ошибка",
    "err_system_body": "Произошла ошибка в ядре вычислений:\n{err}",
    "report_empty_title": "Отчёт пуст",
    "report_empty_body": "Сначала нажмите «Рассчитать спецификацию».",
    "save_ok_title": "Успешно",
    "save_ok_body": "Отчёт сохранён!",
    "save_ok_body_path": "Отчёт сохранён в:\n{path}",
    "save_err_title": "Ошибка сохранения",
    "save_err_body": "Не удалось сохранить: {err}",

    "selftest_calc_title": "Self-test калькулятора",
    "selftest_calc_fail_title": "Self-test калькулятора провален",
    "selftest_probe_title": "Self-test сетевого зонда",
    "selftest_probe_fail_title": "Self-test сетевого зонда провален",

    "probe_settings": "Настройки зонда",
    "probe_ip_label": "IP-адрес (интерфейс):",
    "probe_port_label": "Порт (Art-Net = 6454):",
    "probe_start": "Запустить зонд",
    "probe_stop": "Остановить зонд",
    "probe_status_stopped": "Статус: остановлен",
    "probe_status_listening": "Статус: слушаем сеть...",
    "probe_log_frame": "Состояние сети (обновляется каждую секунду)",
    "probe_port_error_title": "Ошибка",
    "probe_port_error_body": "Порт должен быть числом!",
    "probe_bind_error_title": "Ошибка сети",
    "probe_bind_error_body": "Не удалось привязать порт: {err}",
    "probe_listening": "Слушаем Art-Net на {ip}:{port}. Ждём трафик...",
    "probe_no_traffic": ("Трафик Art-Net не обнаружен.\n"
                         "Проверьте VLAN, брандмауэр на UDP 6454 и адрес назначения отправителя."),
    "probe_final_header": "Финальный отчёт:\n",
    "probe_live_header": "Текущее состояние (обновляется):\n",
    "probe_verdict_label": "ВЕРДИКТ: {verdict}",
    "probe_verdict_bad": "ПЛОХО - сеть не готова к показу (потери или джиттер выше одного кадра DMX)",
    "probe_verdict_warn": "ХОРОШО, но были перезапуски источника (см. ниже) - не влияет на вердикт",
    "probe_verdict_ok": "ХОРОШО - потерь и джиттера в пределах нормы",
    "probe_resets_note": ("Перезапуски источника обнаружены: {count}. Это не потеря кадров - "
                         "счётчик источника (например, пульта) просто начался заново после "
                         "перезагрузки. В вердикт не засчитывается."),
    "probe_non_artdmx_note": "Не-Art-Net пакетов на этом порту: {count}",
    "probe_row": ("Universe {universe:>3}  |  {packets:>5} пакетов  |  {hz:>5.1f} Гц  |  "
                 "потери: {dropped:>3}  дубли: {dup:>2}  перезапуски: {resets:>2}  |  "
                 "джиттер p99: {p99:>5.2f} мс"),
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": _EN,
    "ru": _RU,
}

# ---------------------------------------------------------------------------
# Verdict translations
# ---------------------------------------------------------------------------
# stage_rig_calculator.py's engineering verdicts (e.g. "LIGHT DEFICIT - add
# infrared illumination or faster glass") stay fixed English in the report
# itself - the calculation engine is shared and its wording must read
# identically for every language, see stage_rig_gui.py's module docstring.
#
# This table is a SEPARATE, purely cosmetic layer on top of that: for any
# non-English interface language, the GUI looks the exact English verdict
# string up here and appends the result in parentheses, in a smaller font,
# right after the English original. A verdict or language missing from this
# table simply gets no parenthetical - same safe-fallback philosophy as
# TRANSLATIONS above, just one level more granular (per string, not per key).
#
# Adding a language: add its code as a value-dict key wherever you have a
# translation ready. You do not need to fill in every verdict string for a
# new language on day one.
VERDICT_TRANSLATIONS: dict[str, dict[str, str]] = {
    "subject resolution comfortable": {
        "ru": "разрешение фигуры комфортное",
    },
    "subject resolution minimally sufficient": {
        "ru": "разрешение фигуры минимально достаточное",
    },
    "SUBJECT RESOLUTION TOO LOW - bigger sensor or tighter zones": {
        "ru": "РАЗРЕШЕНИЕ ФИГУРЫ СЛИШКОМ НИЗКОЕ — сенсор крупнее или зоны теснее",
    },
    "LIGHT SUFFICIENT": {
        "ru": "СВЕТА ДОСТАТОЧНО",
    },
    "LIGHT DEFICIT - add infrared illumination or faster glass": {
        "ru": "НЕХВАТКА СВЕТА — добавьте ИК-подсветку или светосильную оптику",
    },
    "EXCEEDS 1 GbE per camera - needs 2.5/5/10 GbE, lower rate, or compression": {
        "ru": "ПРЕВЫШАЕТ 1 GbE на камеру — нужен 2.5/5/10 GbE, ниже частота кадров, или сжатие",
    },
    "1 GbE above 70 percent - drop risk, leave headroom": {
        "ru": "1 GbE выше 70% — риск потерь пакетов, оставьте запас",
    },
    "1 GbE per camera is sufficient": {
        "ru": "1 GbE на камеру достаточно",
    },
    "10 GbE uplink saturated - use 25 GbE or two network cards": {
        "ru": "аплинк 10 GbE перегружен — нужен 25 GbE или две сетевые карты",
    },
    "server uplink must be 10 GbE": {
        "ru": "аплинк сервера должен быть 10 GbE",
    },
    "1 GbE uplink is sufficient": {
        "ru": "аплинка 1 GbE достаточно",
    },
    "BRIGHTNESS SUFFICIENT": {
        "ru": "ЯРКОСТИ ДОСТАТОЧНО",
    },
    "TOO DIM - raise output, shrink the surface, or choose higher gain": {
        "ru": "СЛИШКОМ ТУСКЛО — повысьте яркость, уменьшите экран или возьмите gain выше",
    },
    "EXCELLENT - tight synchrony achievable": {
        "ru": "ОТЛИЧНО — достижима высокая синхронность",
    },
    "ACCEPTABLE - needs prediction and latency-aware choreography": {
        "ru": "ПРИЕМЛЕМО — нужны предсказание и хореография с учётом задержки",
    },
    "CRITICAL - trailing aesthetics only, no precise accents": {
        "ru": "КРИТИЧНО — только фоновая эстетика, без точных акцентов",
    },
}


class Translator:
    """
    Callable translation lookup with automatic English fallback and a
    listener mechanism so a GUI can retranslate its widgets live when the
    language changes, instead of requiring a restart.
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self.language = language if language in TRANSLATIONS else DEFAULT_LANGUAGE
        self._listeners: list = []

    def available_languages(self) -> dict[str, str]:
        return dict(LANGUAGES)

    def add_listener(self, callback) -> None:
        """callback() is invoked with no arguments whenever the language changes."""
        self._listeners.append(callback)

    def set_language(self, language: str) -> None:
        if language not in TRANSLATIONS:
            raise ValueError(f"Unknown language code {language!r}; known: {sorted(TRANSLATIONS)}")
        if language == self.language:
            return
        self.language = language
        for callback in list(self._listeners):
            callback()

    def translate_verdict(self, english_text: str) -> str | None:
        """Small parenthetical translation of a fixed engine verdict string
        (see VERDICT_TRANSLATIONS above), for the current language. Returns
        None when the interface is in English (nothing to add) or when no
        translation exists yet for this exact string/language pair - the
        caller should simply omit the parenthetical in that case."""
        if self.language == DEFAULT_LANGUAGE:
            return None
        return VERDICT_TRANSLATIONS.get(english_text, {}).get(self.language)

    def __call__(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(self.language, {})
        text = table.get(key)
        if text is None:
            # Fall back to English rather than showing a raw key or crashing -
            # this is what makes a half-finished new language safe to ship.
            text = _EN.get(key, key)
        return text.format(**kwargs) if kwargs else text

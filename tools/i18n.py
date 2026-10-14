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
    label_text = t("field_width", unit="m")    # looked up, with fallback

    # Formatting: pass keyword arguments, applied with str.format()
    t("probe_listening", ip="0.0.0.0", port=6454)

Adding a language
------------------
Add a new entry to LANGUAGES (code -> display name) and a new dict to
TRANSLATIONS (code -> {key: text}). You do not need to translate every
key on day one - untranslated keys silently show English until someone
fills them in. Keep the same {placeholders} as the English source string
for any key you do translate, or str.format() will raise at render time.

Units (metric/imperial) are a separate, orthogonal concern handled by
units.py and the small number of {unit}-parameterised keys below (the
length field labels, and the unit_* keys) - see units.py's own docstring
for why unit conversion lives outside the calculation engine entirely.

Part of the Live Stage Toolkit. MIT licence.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"

# Display names shown in the language switcher itself - each language names
# itself, not translated through the table below.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "ru": "Русский",
    "fr": "Français",
    "zh": "中文",
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
    "menu_units": "Units",
    "units_metric": "Metric",
    "units_imperial": "Imperial (US)",
    "menu_theme": "Theme",
    "theme_standard": "Standard",
    "theme_dark": "Dark",
    "theme_light": "Light",

    # --- Unit words, used inside other keys via {unit}/direct lookup ---
    "unit_m": "m",
    "unit_ft": "ft",
    "unit_lux": "lux",
    "unit_fc": "fc",

    # --- Tabs ---
    "tab_calculator": "Calculator (Mocap & Projection)",
    "tab_probe": "Art-Net Network Probe",

    # --- Calculator tab: section frames ---
    "frame_stage": "Stage & Geometry",
    "frame_capture": "Motion Capture (Markerless AI)",
    "frame_projection": "Stage Projection",
    "frame_verdict": "ENGINEERING CORE VERDICT",

    # --- Calculator tab: field labels ---
    # The six length fields carry a {unit} placeholder - filled in at render
    # time with unit_m or unit_ft depending on the active unit system (see
    # stage_rig_gui.py's _unit_word()). Every other field is unit-independent
    # (counts, f-numbers, ISO, percentages, mm focal length, degrees) and
    # keeps a plain, non-parameterised label.
    "field_width": "Width ({unit}):",
    "field_depth": "Depth ({unit}):",
    "field_rig_height": "Truss height ({unit}):",
    "field_inset": "Camera inset ({unit}):",
    "field_performers": "Performers:",
    "field_cameras": "Cameras:",
    "field_sensor": "Sensor:",
    "field_fps": "Frame rate (FPS):",
    "field_aperture": "Aperture (f/):",
    "field_iso": "ISO (gain):",
    "field_screen_width": "Screen width ({unit}):",
    "field_screen_height": "Screen height ({unit}):",
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
    # {volume} and {lux} arrive pre-formatted WITH their unit suffix already
    # attached (see stage_rig_gui.py's _format_length_pair()/
    # _format_illuminance()) - the template itself no longer hardcodes a
    # unit word, so it reads correctly under either unit system.
    "report_header": "=== BASELINE INSTALLATION PARAMETERS ===",
    "report_scene_line": "Stage: {volume} | Performers: {performers} | Cameras: {cameras}",
    "report_sensor_line": "Sensor: {sensor} (Global shutter: {gs})",
    "yes": "Yes",
    "no": "No - PWM banding risk",
    "report_section_1": "--- 1. OPTICS AND AI TRACKING ---",
    "report_lens": "\u2022 Recommended lens: {focal} mm (FOV: {h_fov}\u00b0 x {v_fov}\u00b0)",
    "report_person_px": "\u2022 Performer figure (far corner): {px} px",
    "report_tracking_verdict": "\u2022 Tracking verdict: {verdict}",
    "report_section_2": "--- 2. EXPOSURE AND MOTION ---",
    "report_max_exposure": "\u2022 Max. exposure for sharp hands: {ms} ms",
    "report_required_light": "\u2022 Required light (at f/{f_number}, ISO {iso}): {lux}",
    "report_light_verdict": "\u2022 Light verdict: {verdict}",
    "report_section_3": "--- 3. NETWORK ---",
    "report_per_camera": "\u2022 Per-camera stream: {gbps} Gbit/s",
    "report_uplink_verdict": "\u2022 Server uplink verdict: {verdict}",
    "report_section_4": "--- 4. AVATAR PROJECTION ---",
    "report_effective_lumens": "\u2022 Effective luminous flux: {lumens} lm",
    "report_screen_illuminance": "\u2022 Surface illuminance: {lux}",
    "report_brightness_verdict": "\u2022 Brightness verdict: {verdict}",
    "report_section_5": "--- 5. END-TO-END LATENCY ---",
    "report_latency_path": "\u2022 (Camera -> AI -> Unreal Engine -> Projector)",
    "report_latency_estimate": "\u2022 Estimate: {ms} ms - {verdict}",

    # --- Calculator: dialogs ---
    "err_input_title": "Input error",
    # Updated 2026-10-07 (found live, after French was added): a comma
    # has been an accepted decimal separator too since units.
    # parse_float() replaced the raw float() call in calculate() - the
    # old wording ("decimals use a period") was no longer accurate and
    # actively misleading once that fix landed.
    "err_input_body": ("Please make sure every field contains a number "
                       "(e.g. 7.5 or 7,5), with only one decimal separator - "
                       "not a thousands separator."),
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
    "menu_units": "Единицы",
    "units_metric": "Метрическая",
    "units_imperial": "Имперская (США)",
    "menu_theme": "Тема",
    "theme_standard": "Стандартная",
    "theme_dark": "Тёмная",
    "theme_light": "Светлая",

    "unit_m": "м",
    "unit_ft": "фут",
    "unit_lux": "люкс",
    "unit_fc": "фут-кд",

    "tab_calculator": "Калькулятор (Mocap & Проекция)",
    "tab_probe": "Сетевой зонд Art-Net",

    "frame_stage": "Сцена и геометрия",
    "frame_capture": "Захват движений (Markerless AI)",
    "frame_projection": "Проекция на сцене",
    "frame_verdict": "ВЕРДИКТ ИНЖЕНЕРНОГО ЯДРА",

    "field_width": "Ширина ({unit}):",
    "field_depth": "Глубина ({unit}):",
    "field_rig_height": "Высота ферм ({unit}):",
    "field_inset": "Отступ камер ({unit}):",
    "field_performers": "Танцовщиков:",
    "field_cameras": "Камер:",
    "field_sensor": "Сенсор:",
    "field_fps": "Кадров/с (FPS):",
    "field_aperture": "Светосила (f/):",
    "field_iso": "ISO (усиление):",
    "field_screen_width": "Ширина экрана ({unit}):",
    "field_screen_height": "Высота экрана ({unit}):",
    "field_projectors": "Проекторов:",
    "field_lumens": "Люмен (каждый):",
    "field_surface": "Поверхность:",
    "field_overlap": "Перекрытие сшивки (%):",

    "surface_scrim": "Металлизированная сетка (Gain 0.15)",
    "surface_matte": "Белый матовый (Gain 1.0)",

    "btn_calculate": "Рассчитать спецификацию",
    "btn_export": "Экспорт отчёта",

    "report_header": "=== БАЗОВЫЕ ПАРАМЕТРЫ УСТАНОВКИ ===",
    "report_scene_line": "Сцена: {volume} | Исполнителей: {performers} | Камер: {cameras}",
    "report_sensor_line": "Сенсор: {sensor} (Глобальный затвор: {gs})",
    "yes": "Да",
    "no": "Нет - риск ШИМ",
    "report_section_1": "--- 1. ОПТИКА И AI ТРЕКИНГ ---",
    "report_lens": "\u2022 Рекомендуемый объектив: {focal} мм (FOV: {h_fov}\u00b0 x {v_fov}\u00b0)",
    "report_person_px": "\u2022 Фигура танцовщика (в дальнем углу): {px} px",
    "report_tracking_verdict": "\u2022 Вердикт трекинга: {verdict}",
    "report_section_2": "--- 2. ЭКСПОЗИЦИЯ И ДВИЖЕНИЕ ---",
    "report_max_exposure": "\u2022 Макс. выдержка для резких рук: {ms} мс",
    "report_required_light": "\u2022 Требуемый свет (при f/{f_number}, ISO {iso}): {lux}",
    "report_light_verdict": "\u2022 Вердикт света: {verdict}",
    "report_section_3": "--- 3. СЕТЬ ---",
    "report_per_camera": "\u2022 Поток с 1 камеры: {gbps} Гбит/с",
    "report_uplink_verdict": "\u2022 Вердикт Uplink сервера: {verdict}",
    "report_section_4": "--- 4. ПРОЕКЦИЯ АВАТАРОВ ---",
    "report_effective_lumens": "\u2022 Эффективный световой поток: {lumens} lm",
    "report_screen_illuminance": "\u2022 Освещённость на поверхности: {lux}",
    "report_brightness_verdict": "\u2022 Вердикт по яркости: {verdict}",
    "report_section_5": "--- 5. ОБЩАЯ ЗАДЕРЖКА (End-to-End Latency) ---",
    "report_latency_path": "\u2022 (Camera -> AI -> Unreal Engine -> Projector)",
    "report_latency_estimate": "\u2022 Оценка: {ms} мс - {verdict}",

    "err_input_title": "Ошибка ввода",
    "err_input_body": ("Убедитесь, что во всех полях введены числа (например, 7.5 или 7,5) "
                       "и только один разделитель дробной части - не разделитель тысяч."),
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

# French translation. Kept as a full, complete set, same bar as Russian
# above - not a partial stub (the module docstring explains why a partial
# dict is also safe, but this one was written complete from the start).
_FR: dict[str, str] = {
    "app_title": "Calculateur technique : Capture de mouvement et projection",
    "menu_diagnostics": "Diagnostic",
    "menu_diag_calc": "Tester le calculateur (auto-test)",
    "menu_diag_probe": "Tester la sonde réseau (auto-test)",
    "menu_language": "Langue",
    "menu_units": "Unités",
    "units_metric": "Métrique",
    "units_imperial": "Impérial (US)",
    "menu_theme": "Thème",
    "theme_standard": "Standard",
    "theme_dark": "Sombre",
    "theme_light": "Clair",

    "unit_m": "m",
    "unit_ft": "pi",
    "unit_lux": "lux",
    "unit_fc": "fc",

    "tab_calculator": "Calculateur (Mocap et projection)",
    "tab_probe": "Sonde réseau Art-Net",

    "frame_stage": "Scène et géométrie",
    "frame_capture": "Capture de mouvement (IA sans marqueurs)",
    "frame_projection": "Projection scénique",
    "frame_verdict": "VERDICT DU NOYAU D'INGÉNIERIE",

    "field_width": "Largeur ({unit}) :",
    "field_depth": "Profondeur ({unit}) :",
    "field_rig_height": "Hauteur de la ferme ({unit}) :",
    "field_inset": "Retrait des caméras ({unit}) :",
    "field_performers": "Interprètes :",
    "field_cameras": "Caméras :",
    "field_sensor": "Capteur :",
    "field_fps": "Cadence (ips) :",
    "field_aperture": "Ouverture (f/) :",
    "field_iso": "ISO (gain) :",
    "field_screen_width": "Largeur d'écran ({unit}) :",
    "field_screen_height": "Hauteur d'écran ({unit}) :",
    "field_projectors": "Projecteurs :",
    "field_lumens": "Lumens (chacun) :",
    "field_surface": "Surface :",
    "field_overlap": "Chevauchement de fondu (%) :",

    "surface_scrim": "Toile métallisée (Gain 0,15)",
    "surface_matte": "Mat blanc (Gain 1,0)",

    "btn_calculate": "Calculer la spécification",
    "btn_export": "Exporter le rapport",

    "report_header": "=== PARAMÈTRES D'INSTALLATION DE BASE ===",
    "report_scene_line": "Scène : {volume} | Interprètes : {performers} | Caméras : {cameras}",
    "report_sensor_line": "Capteur : {sensor} (Obturateur global : {gs})",
    "yes": "Oui",
    "no": "Non - risque de scintillement PWM",
    "report_section_1": "--- 1. OPTIQUE ET SUIVI IA ---",
    "report_lens": "• Objectif recommandé : {focal} mm (champ de vision : {h_fov}° x {v_fov}°)",
    "report_person_px": "• Silhouette de l'interprète (coin le plus éloigné) : {px} px",
    "report_tracking_verdict": "• Verdict de suivi : {verdict}",
    "report_section_2": "--- 2. EXPOSITION ET MOUVEMENT ---",
    "report_max_exposure": "• Exposition max. pour des mains nettes : {ms} ms",
    "report_required_light": "• Lumière requise (à f/{f_number}, ISO {iso}) : {lux}",
    "report_light_verdict": "• Verdict de lumière : {verdict}",
    "report_section_3": "--- 3. RÉSEAU ---",
    "report_per_camera": "• Flux par caméra : {gbps} Gbit/s",
    "report_uplink_verdict": "• Verdict de liaison montante serveur : {verdict}",
    "report_section_4": "--- 4. PROJECTION DE L'AVATAR ---",
    "report_effective_lumens": "• Flux lumineux effectif : {lumens} lm",
    "report_screen_illuminance": "• Éclairement de la surface : {lux}",
    "report_brightness_verdict": "• Verdict de luminosité : {verdict}",
    "report_section_5": "--- 5. LATENCE DE BOUT EN BOUT ---",
    "report_latency_path": "• (Caméra -> IA -> Unreal Engine -> Projecteur)",
    "report_latency_estimate": "• Estimation : {ms} ms - {verdict}",

    "err_input_title": "Erreur de saisie",
    "err_input_body": ("Veuillez vous assurer que chaque champ contient un nombre "
                       "(par ex. 7.5 ou 7,5), avec un seul séparateur décimal - "
                       "pas un séparateur de milliers."),
    "err_validation_title": "Vérifiez les valeurs",
    "err_system_title": "Erreur système",
    "err_system_body": "Une erreur est survenue dans le moteur de calcul :\n{err}",
    "report_empty_title": "Le rapport est vide",
    "report_empty_body": "Cliquez d'abord sur « Calculer la spécification ».",
    "save_ok_title": "Enregistré",
    "save_ok_body": "Rapport enregistré !",
    "save_ok_body_path": "Rapport enregistré dans :\n{path}",
    "save_err_title": "Erreur d'enregistrement",
    "save_err_body": "Impossible d'enregistrer : {err}",

    "selftest_calc_title": "Auto-test du calculateur",
    "selftest_calc_fail_title": "Auto-test du calculateur échoué",
    "selftest_probe_title": "Auto-test de la sonde réseau",
    "selftest_probe_fail_title": "Auto-test de la sonde réseau échoué",

    "probe_settings": "Paramètres de la sonde",
    "probe_ip_label": "Adresse IP (interface) :",
    "probe_port_label": "Port (Art-Net = 6454) :",
    "probe_start": "Démarrer la sonde",
    "probe_stop": "Arrêter la sonde",
    "probe_status_stopped": "Statut : arrêtée",
    "probe_status_listening": "Statut : en écoute...",
    "probe_log_frame": "État du réseau (mise à jour chaque seconde)",
    "probe_port_error_title": "Erreur",
    "probe_port_error_body": "Le port doit être un nombre !",
    "probe_bind_error_title": "Erreur réseau",
    "probe_bind_error_body": "Impossible de lier le port : {err}",
    "probe_listening": "Écoute du trafic Art-Net sur {ip}:{port}. En attente de trafic...",
    "probe_no_traffic": ("Aucun trafic Art-Net détecté.\n"
                         "Vérifiez le VLAN, le pare-feu sur UDP 6454, et l'adresse cible de l'émetteur."),
    "probe_final_header": "Rapport final :\n",
    "probe_live_header": "État actuel (mise à jour) :\n",
    "probe_verdict_label": "VERDICT : {verdict}",
    "probe_verdict_bad": ("MAUVAIS - le réseau n'est pas prêt pour le spectacle (pertes ou jitter "
                          "au-delà d'une trame DMX)"),
    "probe_verdict_warn": ("BON, mais des redémarrages de l'émetteur ont été détectés (voir "
                           "ci-dessous) - n'affecte pas le verdict"),
    "probe_verdict_ok": "BON - pertes et jitter dans la tolérance du spectacle",
    "probe_resets_note": ("Redémarrages de l'émetteur détectés : {count}. Ce ne sont pas des trames "
                         "perdues - le compteur de la source (par ex. une console) a simplement "
                         "redémarré après un redémarrage. Non comptabilisé dans le verdict."),
    "probe_non_artdmx_note": "Paquets non-Art-Net sur ce port : {count}",
    "probe_row": ("Univers {universe:>3}  |  {packets:>5} paquets  |  {hz:>5.1f} Hz  |  "
                 "pertes : {dropped:>3}  doublons : {dup:>2}  redémarrages : {resets:>2}  |  "
                 "jitter p99 : {p99:>5.2f} ms"),
}

# Simplified Chinese. Kept as a full, complete set, same bar as Russian/
# French above. Added 2026-10-14 for the PUBLIC toolkit only (the
# Architect's own instruction: pilot it here first, roll out to the
# private "Pro" tool separately only once this is confirmed working) -
# see stage_rig_gui.py's own CJK_FONT_FAMILY comment for the font-
# rendering half of this change (a translated string alone is not
# enough - Consolas/Segoe UI/TkDefaultFont have no Han glyphs).
_ZH: dict[str, str] = {
    "app_title": "工程计算器：动作捕捉与投影",
    "menu_diagnostics": "诊断",
    "menu_diag_calc": "测试计算器（自检）",
    "menu_diag_probe": "测试网络探测器（自检）",
    "menu_language": "语言",
    "menu_units": "单位",
    "units_metric": "公制",
    "units_imperial": "英制（美国）",
    "menu_theme": "主题",
    "theme_standard": "标准",
    "theme_dark": "深色",
    "theme_light": "浅色",

    "unit_m": "米",
    "unit_ft": "英尺",
    "unit_lux": "勒克斯",
    "unit_fc": "英尺烛光",

    "tab_calculator": "计算器（动作捕捉与投影）",
    "tab_probe": "Art-Net 网络探测器",

    "frame_stage": "舞台与几何",
    "frame_capture": "动作捕捉（无标记 AI）",
    "frame_projection": "舞台投影",
    "frame_verdict": "工程核心结论",

    "field_width": "宽度（{unit}）：",
    "field_depth": "深度（{unit}）：",
    "field_rig_height": "桁架高度（{unit}）：",
    "field_inset": "摄像机内缩（{unit}）：",
    "field_performers": "演员人数：",
    "field_cameras": "摄像机数量：",
    "field_sensor": "传感器：",
    "field_fps": "帧率（FPS）：",
    "field_aperture": "光圈（f/）：",
    "field_iso": "ISO（增益）：",
    "field_screen_width": "屏幕宽度（{unit}）：",
    "field_screen_height": "屏幕高度（{unit}）：",
    "field_projectors": "投影机数量：",
    "field_lumens": "流明（每台）：",
    "field_surface": "表面：",
    "field_overlap": "融合重叠（%）：",

    "surface_scrim": "金属幕布（增益 0.15）",
    "surface_matte": "白色哑光（增益 1.0）",

    "btn_calculate": "计算规格",
    "btn_export": "导出报告",

    "report_header": "=== 基础安装参数 ===",
    "report_scene_line": "舞台：{volume} | 演员：{performers} | 摄像机：{cameras}",
    "report_sensor_line": "传感器：{sensor}（全局快门：{gs}）",
    "yes": "是",
    "no": "否 - 存在 PWM 频闪风险",
    "report_section_1": "--- 1. 光学与 AI 追踪 ---",
    "report_lens": "• 推荐镜头：{focal} mm（视场角：{h_fov}° x {v_fov}°）",
    "report_person_px": "• 演员轮廓（最远角）：{px} px",
    "report_tracking_verdict": "• 追踪结论：{verdict}",
    "report_section_2": "--- 2. 曝光与运动 ---",
    "report_max_exposure": "• 手部清晰所需最大曝光时间：{ms} ms",
    "report_required_light": "• 所需光照（f/{f_number}，ISO {iso} 下）：{lux}",
    "report_light_verdict": "• 光照结论：{verdict}",
    "report_section_3": "--- 3. 网络 ---",
    "report_per_camera": "• 单台摄像机数据流：{gbps} Gbit/s",
    "report_uplink_verdict": "• 服务器上行结论：{verdict}",
    "report_section_4": "--- 4. 虚拟形象投影 ---",
    "report_effective_lumens": "• 有效光通量：{lumens} lm",
    "report_screen_illuminance": "• 表面照度：{lux}",
    "report_brightness_verdict": "• 亮度结论：{verdict}",
    "report_section_5": "--- 5. 端到端延迟 ---",
    "report_latency_path": "• （摄像机 -> AI -> Unreal Engine -> 投影机）",
    "report_latency_estimate": "• 估计值：{ms} ms - {verdict}",

    "err_input_title": "输入错误",
    "err_input_body": ("请确保每个字段都填写了数字（例如 7.5 或 7,5），"
                       "且只有一个小数分隔符——不是千位分隔符。"),
    "err_validation_title": "请检查数值",
    "err_system_title": "系统错误",
    "err_system_body": "计算核心发生错误：\n{err}",
    "report_empty_title": "报告为空",
    "report_empty_body": "请先点击“计算规格”。",
    "save_ok_title": "已保存",
    "save_ok_body": "报告已保存！",
    "save_ok_body_path": "报告已保存到：\n{path}",
    "save_err_title": "保存错误",
    "save_err_body": "无法保存：{err}",

    "selftest_calc_title": "计算器自检",
    "selftest_calc_fail_title": "计算器自检失败",
    "selftest_probe_title": "网络探测器自检",
    "selftest_probe_fail_title": "网络探测器自检失败",

    "probe_settings": "探测器设置",
    "probe_ip_label": "IP 地址（接口）：",
    "probe_port_label": "端口（Art-Net = 6454）：",
    "probe_start": "启动探测器",
    "probe_stop": "停止探测器",
    "probe_status_stopped": "状态：已停止",
    "probe_status_listening": "状态：正在监听...",
    "probe_log_frame": "网络状态（每秒更新）",
    "probe_port_error_title": "错误",
    "probe_port_error_body": "端口必须是数字！",
    "probe_bind_error_title": "网络错误",
    "probe_bind_error_body": "无法绑定端口：{err}",
    "probe_listening": "正在 {ip}:{port} 上监听 Art-Net。等待流量...",
    "probe_no_traffic": ("未检测到 Art-Net 流量。\n"
                         "请检查 VLAN、UDP 6454 端口的防火墙设置，以及发送方的目标地址。"),
    "probe_final_header": "最终报告：\n",
    "probe_live_header": "当前状态（更新中）：\n",
    "probe_verdict_label": "结论：{verdict}",
    "probe_verdict_bad": "差 - 网络未达到演出要求（丢包或抖动超过一个 DMX 帧）",
    "probe_verdict_warn": "良好，但检测到发送方重启（见下文）- 不影响结论",
    "probe_verdict_ok": "良好 - 丢包和抖动在演出容许范围内",
    "probe_resets_note": ("检测到发送方重启：{count} 次。这不是丢帧——源设备（例如调光台）的"
                         "计数器在重启后简单地重新开始计数。不计入结论。"),
    "probe_non_artdmx_note": "此端口上的非 Art-Net 数据包：{count}",
    "probe_row": ("Universe {universe:>3}  |  {packets:>5} 个数据包  |  {hz:>5.1f} Hz  |  "
                 "丢失：{dropped:>3}  重复：{dup:>2}  重启：{resets:>2}  |  "
                 "p99 抖动：{p99:>5.2f} ms"),
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": _EN,
    "ru": _RU,
    "fr": _FR,
    "zh": _ZH,
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
        "fr": "résolution du sujet confortable",
        "zh": "主体分辨率充足",
    },
    "subject resolution minimally sufficient": {
        "ru": "разрешение фигуры минимально достаточное",
        "fr": "résolution du sujet minimalement suffisante",
        "zh": "主体分辨率勉强足够",
    },
    "SUBJECT RESOLUTION TOO LOW - bigger sensor or tighter zones": {
        "ru": "РАЗРЕШЕНИЕ ФИГУРЫ СЛИШКОМ НИЗКОЕ — сенсор крупнее или зоны теснее",
        "fr": "RÉSOLUTION DU SUJET TROP FAIBLE — capteur plus grand ou zones plus resserrées",
        "zh": "主体分辨率过低——需要更大传感器或缩小捕捉区域",
    },
    "LIGHT SUFFICIENT": {
        "ru": "СВЕТА ДОСТАТОЧНО",
        "fr": "LUMIÈRE SUFFISANTE",
        "zh": "光照充足",
    },
    "LIGHT DEFICIT - add infrared illumination or faster glass": {
        "ru": "НЕХВАТКА СВЕТА — добавьте ИК-подсветку или светосильную оптику",
        "fr": "DÉFICIT DE LUMIÈRE — ajoutez un éclairage infrarouge ou une optique plus lumineuse",
        "zh": "光照不足——请增加红外照明或使用更大光圈镜头",
    },
    "EXCEEDS 1 GbE per camera - needs 2.5/5/10 GbE, lower rate, or compression": {
        "ru": "ПРЕВЫШАЕТ 1 GbE на камеру — нужен 2.5/5/10 GbE, ниже частота кадров, или сжатие",
        "fr": ("DÉPASSE 1 GbE par caméra — nécessite 2,5/5/10 GbE, une cadence plus basse, "
              "ou de la compression"),
        "zh": "超过每摄像机 1 GbE——需要 2.5/5/10 GbE、降低帧率或压缩",
    },
    "1 GbE above 70 percent - drop risk, leave headroom": {
        "ru": "1 GbE выше 70% — риск потерь пакетов, оставьте запас",
        "fr": "1 GbE au-dessus de 70 % — risque de perte, prévoyez une marge",
        "zh": "1 GbE 负载超过 70%——有丢包风险，请留出余量",
    },
    "1 GbE per camera is sufficient": {
        "ru": "1 GbE на камеру достаточно",
        "fr": "1 GbE par caméra est suffisant",
        "zh": "每摄像机 1 GbE 已足够",
    },
    "10 GbE uplink saturated - use 25 GbE or two network cards": {
        "ru": "аплинк 10 GbE перегружен — нужен 25 GbE или две сетевые карты",
        "fr": "liaison montante 10 GbE saturée — utilisez 25 GbE ou deux cartes réseau",
        "zh": "10 GbE 上行已饱和——请使用 25 GbE 或两块网卡",
    },
    "server uplink must be 10 GbE": {
        "ru": "аплинк сервера должен быть 10 GbE",
        "fr": "la liaison montante du serveur doit être en 10 GbE",
        "zh": "服务器上行必须为 10 GbE",
    },
    "1 GbE uplink is sufficient": {
        "ru": "аплинка 1 GbE достаточно",
        "fr": "une liaison montante 1 GbE est suffisante",
        "zh": "1 GbE 上行已足够",
    },
    "BRIGHTNESS SUFFICIENT": {
        "ru": "ЯРКОСТИ ДОСТАТОЧНО",
        "fr": "LUMINOSITÉ SUFFISANTE",
        "zh": "亮度充足",
    },
    "TOO DIM - raise output, shrink the surface, or choose higher gain": {
        "ru": "СЛИШКОМ ТУСКЛО — повысьте яркость, уменьшите экран или возьмите gain выше",
        "fr": "TROP SOMBRE — augmentez la puissance, réduisez la surface, ou choisissez un gain plus élevé",
        "zh": "太暗——请提高输出、缩小屏幕尺寸或选择更高增益",
    },
    "EXCELLENT - tight synchrony achievable": {
        "ru": "ОТЛИЧНО — достижима высокая синхронность",
        "fr": "EXCELLENT — une synchronisation précise est réalisable",
        "zh": "优秀——可实现高精度同步",
    },
    "ACCEPTABLE - needs prediction and latency-aware choreography": {
        "ru": "ПРИЕМЛЕМО — нужны предсказание и хореография с учётом задержки",
        "zh": "可接受——需要预测和考虑延迟的编舞设计",
        "fr": "ACCEPTABLE — nécessite une prédiction et une chorégraphie tenant compte de la latence",
    },
    "CRITICAL - trailing aesthetics only, no precise accents": {
        "ru": "КРИТИЧНО — только фоновая эстетика, без точных акцентов",
        "fr": "CRITIQUE — esthétique de fond uniquement, pas d'accents précis",
        "zh": "严重——仅适合营造氛围效果，无法实现精确动作同步",
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


_PLACEHOLDER_RE = __import__("re").compile(r"\{(\w+)(?::[^}]*)?\}")


def _placeholders(text: str) -> set[str]:
    """Names inside {..} in `text`, format-spec (":>5.1f" etc.) stripped -
    e.g. "{hz:>5.1f} Hz" -> {"hz"}. Used by selftest() below to confirm a
    translated string takes exactly the same .format() arguments as its
    English original, not just that a translation exists at all - a
    typo'd/missing placeholder would otherwise only surface the first
    time that exact key is rendered with real data, in whichever
    language happens to hit it."""
    return set(_PLACEHOLDER_RE.findall(text))


def selftest() -> int:
    # Added 2026-10-14 alongside Chinese (zh) - this module never had its
    # own self-test before (unlike units.py); the module's own docstring
    # already claims "every language dict is allowed to be a partial
    # subset" of English, en/ru/fr/zh are each documented ABOVE as "kept
    # as a full, complete set" instead, a stronger claim worth actually
    # checking rather than trusting the comment alone.
    assert "zh" in LANGUAGES and "zh" in TRANSLATIONS, \
        "Chinese must be registered in both LANGUAGES (switcher) and TRANSLATIONS (strings)"

    en_keys = set(_EN)
    for lang, table in TRANSLATIONS.items():
        if lang == "en":
            continue
        missing = en_keys - set(table)
        assert not missing, f"{lang}: missing keys (falls back to English): {sorted(missing)}"
        for key in en_keys:
            en_placeholders = _placeholders(_EN[key])
            lang_placeholders = _placeholders(table[key])
            assert en_placeholders == lang_placeholders, (
                f"{lang}.{key!r}: placeholder mismatch - English wants {sorted(en_placeholders)}, "
                f"got {sorted(lang_placeholders)} ({table[key]!r})")

    # translate_verdict() - a real round trip through the Translator, not
    # just a dict-literal check above, for one representative zh entry
    # (same mechanism en/ru/fr already use, just the newest column).
    t = Translator()
    t.set_language("zh")
    assert t.translate_verdict("LIGHT SUFFICIENT") == "光照充足"
    assert t.translate_verdict("a string with no zh translation yet") is None
    t.set_language("en")
    assert t.translate_verdict("LIGHT SUFFICIENT") is None, \
        "English must never show a parenthetical - it IS the original"

    # __call__()'s own English-fallback path (a key present in English
    # but missing from some OTHER language) - every key is complete for
    # zh today, so there is no real gap to exercise this on; punch one
    # temporarily rather than skipping the check.
    t.set_language("zh")
    assert t("app_title") == _ZH["app_title"], "a real zh key must render in zh, not fall back to English"
    saved = TRANSLATIONS["zh"].pop("app_title")
    try:
        assert t("app_title") == _EN["app_title"], \
            "a key missing from zh must fall back to English, not a raw key name or a crash"
    finally:
        TRANSLATIONS["zh"]["app_title"] = saved

    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())

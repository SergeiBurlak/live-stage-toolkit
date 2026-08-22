Live Stage Performance Toolkit

Open engineering tools for creating markerless, real-time motion capture and output systems for theatrical productions using Unreal Engine 5.

These tools were developed for the theatrical production *Queen Anne*, in which live dancers control digital performers generated in real-time and projected onto the stage. They have been made publicly available.

Why this exists

A markerless motion capture system works well in a studio. A theater is not a studio. The stage is dark, lights flicker, fixtures change color every few seconds, and performers move rapidly. Most questions determining the viability of such a system can be answered through arithmetic calculations before spending any money:

How many cameras are needed, with what focal lengths, and at what height?
How many pixels of body height will be visible from the furthest corner of the stage?
How short must the shutter speed be to avoid motion blur, and how much light is required for that?
Will the camera video streams fit within the network bandwidth?
How bright will the projected image be on this surface?
What latency will the audience experience?

This toolkit provides numerical answers to these questions and supplies the runtime components necessary for the reliable execution of the show.

Tools
tools/stage_rig_calculator.py

Calculates the complete engineering specifications for the stage motion capture and projection system. Requires no dependencies other than the standard Python library. Example output for a 5 x 5 m capture area, using 5-megapixel global shutter cameras:

Near / center / far distance ................. 3.57 / 5.50 / 9.18 m
Required horizontal field of view ............ 70°
Recommended focal length ..................... 6.0 mm
Subject height in pixels (far point) ......... 339 pixels
Maximum exposure for
Required scene illumination: ................. 64 lux
Network load per camera ...................... 2.406
Sender-to-receiver latency ................... 187.7 ms

Run it:

python3 stage_rig_calculator.py --width 7 --depth 6 --rig-height 4.5 \
--performers 4

Self-test:

python3 stage_rig_calculator.py --selftest
tools/artnet_probe.py

Show-network quality control system. It accepts UDP packets on port 6454, decodes Art-Net DMX packets, and provides reports for each broadcast node: effective refresh rate, number of dropped frames (detected via the sequence field), duplicates, out-of-order packets, and inter-packet interval percentiles.

Recommended to run before every rehearsal. If the 99th percentile interval exceeds 1.5 DMX frames, the lighting fixtures will exhibit noticeable jitter.

python3 artnet_probe.py --seconds 30 --nominal-hz 44
unreal/ShowNet/

Unreal Engine subsystem for deterministic Art-Net output. Sending DMX from the game thread means that a rendering failure translates into a lighting failure in front of the audience. This component offloads output to an isolated, fixed-rate thread featuring double-buffered data channels, a watchdog timer that disables all universes if the game thread hangs, an interlocked emergency stop, and a three-frame shutdown sequence to ensure no fixture remains stuck on a stale value.

What to know before buying anything

Use global shutter sensors. LED stage lights control brightness via pulse-width modulation (PWM) at frequencies ranging from hundreds to thousands of hertz. A rolling shutter sensor exposes the image row by row.

Near-infrared (NIR) illumination. At a realistic dancer's hand speed of 6 m/s, limiting motion blur to under two pixels restricts exposure time to approximately 1.76 ms.

Hardware-level synchronization. A 5 ms desynchronization between cameras causes a 30 mm shift for a hand moving at 6 m/s—enough to disrupt triangulation. Hardware synchronization is required.

Check your network before selecting cameras.

Status

Early-stage development. The tools are currently used in the production environment of the project for which they were created. The calculator and probe include self-test functions. Bug reports and pull requests are welcome.

License

MIT. Use, modify, and implement freely.




РУССКИЙ ЯЗЫК:

Набор инструментов для живых выступлений на сцене

Открытые инженерные инструменты для создания систем захвата движений в реальном времени без маркеров и вывода результатов для театральных постановок на Unreal Engine 5.

Эти инструменты были разработаны для театральной постановки «Королева Анна» , в которой живые танцоры управляют цифровыми исполнителями, создаваемыми в реальном времени и проецируемыми на сцену. Они опубликованы.

Почему это существует

Бесконтактная система захвата движений хорошо работает в студии. Театр — это не студия. Сцена темная, свет мерцает, светильники меняют цвет каждые несколько секунд, а исполнители двигаются быстро. На большинство вопросов, определяющих работоспособность такой системы, можно ответить с помощью арифметических вычислений, прежде чем тратить деньги:

Сколько камер, с каким фокусным расстоянием, на какой высоте?
На сколько пикселей по высоте тела это повлечёт за собой дальний угол сцены?
Насколько короткой должна быть выдержка, чтобы избежать размытия изображения из-за движения, и сколько света для этого требуется?
Поместятся ли видеопотоки с камер в сеть?
Насколько ярким будет проецируемое изображение на этой поверхности?
Какую задержку увидят зрители?

Этот набор инструментов дает численные ответы на эти вопросы и предоставляет компоненты среды выполнения, необходимые для безопасного вывода шоу.

Инструменты
tools/stage_rig_calculator.py

Вычисляет полный инженерный бюджет системы захвата и проекции сцены. Не требует зависимостей, кроме стандартной библиотеки Python.

Пример выходных данных для зоны съемки 5 x 5 м, полученных с помощью 5-мегапиксельных камер с глобальным затвором:

Расстояние вблизи / в центре / вдали ......... 3,57 / 5,50 / 9,18 м
Требуемое горизонтальное поле зрения .............. 70
Рекомендуемое фокусное расстояние ............. 6,0 мм
Высота тела в пикселях, дальняя точка ..... 339 пикселей
Максимальная экспозиция для
Требуемая освещенность сцены: ........... 64 люкс
Нагрузка на сеть для каждой камеры .............. 2,406
Задержка от отправителя до получателя ................... 187,7 мс

Запустите его:

python3 stage_rig_calculator.py --width 7 --depth 6 --rig-height 4.5 \
    --исполнители 4

Самопроверка:

python3 stage_rig_calculator.py --selftest
tools/artnet_probe.py

Система контроля качества Show-network. Принимает UDP-пакеты 6454, декодирует пакеты Art-Net DMX и предоставляет отчеты по каждому вещательному узлу: эффективная частота обновления, количество пропущенных кадров, обнаруженных в поле последовательности, дубликаты, пакеты, поступившие не по порядку, и процентили межпакетных интервалов.

Рекомендуется запускать перед каждой репетицией. Если интервал 99-го процентиля превышает полтора кадра DMX, световые приборы будут заметно подергиваться.

python3 artnet_probe.py --seconds 30 --nominal-hz 44
unreal/ShowNet/

Подсистема Unreal Engine для детерминированного вывода Art-Net. Отправка DMX из игрового потока означает, что сбой рендеринга превратится в сбой освещения перед аудиторией. Этот компонент перемещает вывод в изолированный поток с фиксированной скоростью, с двойной буферизацией данных каналов, сторожевым таймером, который отключает все вселенные, если игровой поток зависает, блокируемой аварийной остановкой и тремя кадрами отключения при завершении работы, чтобы ни один прибор не мог зафиксироваться на устаревшем значении.

Что стоит знать, прежде чем что-либо покупать

Используйте датчики с глобальным затвором. Светодиодные сценические светильники регулируют яркость с помощью широтно-импульсной модуляции с частотой от сотен до тысяч герц. Датчик с построчным затвором обеспечивает экспозицию каждого ряда.

Свет в ближнем инфракрасном диапазоне. При реалистичной скорости движения танцевальных рук 6 м/с, при размытии движения менее двух пикселей, экспозиция ограничивается примерно 1,76.

Синхронизация на аппаратном уровне. Десинхронизация между камерами на 5 мс приводит к смещению руки, движущейся со скоростью 6 м/с, на 30 мм, чего достаточно, чтобы нарушить триангуляцию. Аппаратная синхронизация.

Перед выбором камер проверьте сеть. A 5

Статус

На ранней стадии разработки. Инструменты используются в производственной среде в рамках проекта, для которого они были написаны. Калькулятор и зонд включают самотестирование. Приветствуются сообщения об ошибках и запросы на добавление изменений.

Лицензия

MIT. Используйте, изменяйте, внедряйте.

# Building the Windows installer

This is the reproducible recipe behind `LiveStageToolkit-Setup.exe` (see the
[Releases page](https://github.com/SergeiBurlak/live-stage-toolkit/releases/latest)
for a ready-made download - most people do not need this file). It targets
Windows, since that is where the theatre technical staff this GUI is written
for actually work.

## Prerequisites

- Python 3.10+ on Windows.
- [PyInstaller](https://pyinstaller.org/): `pip install pyinstaller`
- [Pillow](https://pillow.readthedocs.io/): `pip install pillow` - only needed
  if you are regenerating `assets/icon.ico` from a new source logo; not
  required to build the exe/installer from the assets already in the repo.
- [Inno Setup 6](https://jrsoftware.org/isdl.php) - free compiler, provides
  `ISCC.exe`. Installs to `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` by
  default.

## Assets

`assets/icon.ico` (multi-resolution: 16/32/48/256) and `assets/logo.png` are
already committed - the GUI reads them at `tools/stage_rig_gui.py`'s
`_resource_path()` (source: sibling `assets/` folder next to `tools/`; frozen
build: bundle root, see the docstring there for why both cases read the same
file). You only need to touch this step if the logo changes.

To regenerate `icon.ico` from a new source image with Pillow:

```python
from PIL import Image
img = Image.open("logo_source.png")
img.save("assets/icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
```

Pad non-square source art to a square canvas first (paste onto a new square
`Image.new("RGBA", (side, side), ...)`) - a non-square source produces
non-square icon frames, which some Windows contexts render oddly.

## Build the executable

From the repository root:

```
pyinstaller -y LiveStageToolkit.spec
```

The checked-in `.spec` file is the source of truth for build flags (window
mode, icon, bundled data). It is equivalent to running PyInstaller fresh with:

```
pyinstaller --windowed --onedir --name LiveStageToolkit ^
    --icon=assets\icon.ico ^
    --add-data "assets\logo.png;." ^
    tools\stage_rig_gui.py
```

Notes on the flags:
- `--windowed` - required, or a console window pops up behind the GUI.
- `--onedir`, not `--onefile` - a onefile build re-extracts itself to a temp
  folder on every launch (noticeable startup delay); onedir starts fast. Use
  `--onefile` instead if you would rather ship a single file and accept the
  slower start.
- `--add-data "assets\logo.png;."` - bundles the banner image so
  `_resource_path()` finds it at the frozen bundle root at runtime; the exe
  icon itself comes from `--icon` and is a separate embedding step.

The four local modules (`stage_rig_calculator`, `artnet_probe`, `i18n`,
`units`) are picked up automatically since they sit next to
`stage_rig_gui.py`. Check `build/LiveStageToolkit/warn-LiveStageToolkit.txt`
for `missing module` warnings if something does not import correctly in the
frozen build - none of these four should ever appear there.

Output: `dist/LiveStageToolkit/LiveStageToolkit.exe` (plus its `_internal/`
support files - the whole `dist/LiveStageToolkit/` folder is one deployable
unit).

## Build the installer

```
cd installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" LiveStageToolkit.iss
```

Output: `installer/Output/LiveStageToolkit-Setup.exe`. Both `dist/`,
`build/`, and `installer/Output/` are git-ignored - only the source `.spec`
and `.iss` recipes are committed, not their generated binaries. Binaries are
distributed as [GitHub Release assets](https://github.com/SergeiBurlak/live-stage-toolkit/releases/latest)
instead.

The installer script installs to Program Files, creates a Start Menu group
and a desktop shortcut (both inherit the icon embedded in the exe by
PyInstaller's `--icon` - no separate icon file is needed for the shortcuts),
registers an Add/Remove Programs entry, and its uninstaller removes
everything cleanly.

## Verify before shipping a new build

- [ ] Logo shows in the header banner and as the window/taskbar icon running
      from source: `python tools\stage_rig_gui.py`.
- [ ] `dist\LiveStageToolkit\LiveStageToolkit.exe` launches with no console
      window, correct icon, and reproduces the same calculator output as the
      source run.
- [ ] `LiveStageToolkit-Setup.exe` compiles without errors.
- [ ] Full manual install/uninstall cycle: run the installer, confirm the
      default install path, desktop shortcut, and Start Menu entry all
      appear with the correct icon; launch the app from the shortcut; then
      uninstall via Add/Remove Programs and confirm the install folder,
      shortcuts, and registry entry are all gone.

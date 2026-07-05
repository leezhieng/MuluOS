# MuluOS Branding Assets

This document describes what to put in [`assets/branding/`](../assets/branding/) and where each asset gets consumed by the build. Currently nothing in the build code reads from this directory — it's a placeholder waiting for assets to be wired up.

## Identity (source-of-truth marks)

| File | Purpose |
|---|---|
| `logo.svg` | Primary MuluOS logo, vector. Everything else can be exported from this. |
| `logo-mono.svg` | Single-color version for places that need it (terminal MOTD, mono icons). |
| `icon-256.png`, `icon-128.png`, `icon-64.png`, `icon-48.png` | PNG exports for the hicolor icon theme. |
| `palette.txt` or `palette.json` | Color hex codes so theming stays consistent across all other files. |

## Boot stage

| File | Purpose |
|---|---|
| `grub-background.png` | 1920×1080. Used as `GRUB_BACKGROUND` in the installed system's `/etc/default/grub`. Wire up in [`muluos/builder/iso.py`](../muluos/builder/iso.py) for the live ISO's GRUB too. |
| `plymouth/` | Directory for a Plymouth boot splash theme (`.plymouth`, `.script`, frame PNGs). Optional. Add `plymouth` and `plymouth-themes` to [`muluos/profiles/base.py`](../muluos/profiles/base.py) if you want this. |

## Login (KDE profile only)

| File | Purpose |
|---|---|
| `sddm-theme/` | Directory containing `metadata.desktop`, `Main.qml`, `theme.conf`, and a background PNG. Copied to `/usr/share/sddm/themes/muluos/` by the chroot hook. |

## Desktop

| File | Purpose |
|---|---|
| `wallpaper-1920x1080.png` | Default desktop background, 1080p. |
| `wallpaper-2560x1440.png` | 1440p variant. |
| `wallpaper-3840x2160.png` | 4K variant. |
| `plasma-lookandfeel/` | KDE "global theme" bundle. Optional — defer until the KDE customization pass. |

At least one wallpaper resolution is required. Installed to `/usr/share/backgrounds/muluos/`.

## Installer (PyQt6 wizard)

| File | Purpose |
|---|---|
| `installer-banner.png` | 164×400 vertical strip shown on the left of each `QWizardPage`. Wire via `wiz.setPixmap(QWizard.WizardPixmap.WatermarkPixmap, ...)` in [`muluos/installer/main.py`](../muluos/installer/main.py). |
| `installer-logo.png` | 64×64 shown in the top-right of each page (`QWizard.WizardPixmap.LogoPixmap`). |
| `installer-background.png` | 1024×768. Optional fullscreen background for the live session running the installer. |

## Misc

| File | Purpose |
|---|---|
| `motd` | Text file shown on CLI login (the `cli` profile). Copied to `/etc/motd`. |
| `os-release` | Overrides `/etc/os-release` with MuluOS identity (`NAME=MuluOS`, `PRETTY_NAME=...`, `HOME_URL=...`). **Important** — without this the installed system still reports itself as Debian. |
| `issue` | Pre-login banner at `/etc/issue`. |

## Minimum viable set

If you just want something that *looks* like MuluOS:

- `logo.svg`
- `wallpaper-1920x1080.png`
- `installer-banner.png`
- `installer-logo.png`
- `os-release`

Everything else can come later.

## Wiring status

None of the assets above are read by the build yet. Once files are added, the consumption points are:

- [`scripts/chroot-hook-debian.sh`](../scripts/chroot-hook-debian.sh) — should copy `os-release`, `motd`, `issue`, wallpapers, SDDM theme, icon PNGs into the rootfs.
- [`muluos/builder/iso.py`](../muluos/builder/iso.py) — should reference `grub-background.png` when writing the live ISO's GRUB config.
- [`muluos/installer/main.py`](../muluos/installer/main.py) — should call `setPixmap` for the banner and logo.

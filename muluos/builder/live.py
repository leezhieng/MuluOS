"""Live-only packages (Debian).

Present in the live ISO so the PyQt6 installer can render, pruned from the
installed target on CLI installs by muluos.installer.backend.install.
No-op on KDE installs since the KDE profile pulls in the same X+Qt stack.
"""
PACKAGES = [
    # X server + session launcher.
    "xserver-xorg", "xinit",

    # Input + keymaps.
    "xserver-xorg-input-libinput",
    "xkb-data", "x11-xkb-utils",

    # Video drivers. modesetting (built into xserver-xorg) handles most modern
    # KMS hardware; these are belt-and-suspenders for older / virtualized HW.
    "xserver-xorg-video-vesa",
    "xserver-xorg-video-intel",
    "xserver-xorg-video-amdgpu",
    "xserver-xorg-video-nouveau",
    "xserver-xorg-video-vmware",
    "libgl1-mesa-dri",

    # Fonts for the installer to render text.
    "fonts-dejavu",

    # X utility used by the live .xinitrc to disable screensaver.
    "x11-xserver-utils",

    # PyQt6 binding for the installer.
    "python3-pyqt6",
]

"""Live-only packages.

Present in the live ISO so the PyQt6 installer can render, pruned from the
installed target on CLI installs by muluos.installer.backend.install.
No-op on KDE installs since the KDE profile pulls in the same X+Qt stack.
"""
PACKAGES = [
    # X server + session launcher.
    "xorg-server", "xinit",

    # Input + keymaps.
    "xf86-input-libinput",
    "xkeyboard-config", "setxkbmap",

    # Video drivers. modesetting (built into xorg-server) handles most modern
    # KMS hardware; these are belt-and-suspenders for older / virtualized HW.
    "xf86-video-vesa",
    "xf86-video-intel",
    "xf86-video-amdgpu",
    "xf86-video-nouveau",
    "xf86-video-vmware",
    "mesa-dri-gallium",

    # Fonts for the installer to render text.
    "font-dejavu",

    # agetty with --autologin for the live tty1 session.
    "util-linux-misc",

    # X utility used by the live .xinitrc to disable screensaver.
    "xset",

    # PyQt6 binding for the installer.
    "py3-qt6",
]

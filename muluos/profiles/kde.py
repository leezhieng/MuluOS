"""Desktop profile: KDE Plasma (Debian). To be heavily customized later."""
NAME = "kde"
PACKAGES = [
    # X server + input
    "xserver-xorg", "xserver-xorg-input-libinput", "libgl1-mesa-dri",
    # KDE Plasma
    "plasma-desktop", "plasma-workspace",
    "sddm", "kde-config-sddm",
    "konsole", "dolphin",
    "kate",
    "firefox-esr",
    # Python Qt6 bindings
    "python3-pyqt6",
    # Audio
    "pipewire", "pipewire-pulse", "wireplumber",
    # Fonts
    "fonts-dejavu", "fonts-liberation",
    # MIME + desktop database
    "shared-mime-info", "desktop-file-utils",
    # Python imaging
    "python3-pillow",
]

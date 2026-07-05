#!/bin/bash
# Runs inside the freshly-bootstrapped Debian rootfs. $1 is the profile name.
# This is the systemd equivalent of the Alpine chroot-hook.sh.
set -eu
PROFILE="${1:-cli}"

# ── Enable essential systemd services ────────────────────────────────────
systemctl enable NetworkManager
systemctl enable ssh

# Make /usr/lib/muluos importable as a Python site dir so apps can
# `import muluos_registry` regardless of which python3.X is installed.
if command -v python3 >/dev/null 2>&1; then
    SITE=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>/dev/null || true)
    if [ -n "$SITE" ]; then
        mkdir -p "$SITE"
        echo "/usr/lib/muluos" > "$SITE/muluos.pth"
    fi
fi

# Enable the registry daemon (needed by every profile).
if [ -f /etc/systemd/system/muluos-registryd.service ]; then
    systemctl enable muluos-registryd
fi

# Regenerate the environment profile on every boot.
if [ -f /etc/systemd/system/muluos-env-generate.service ]; then
    systemctl enable muluos-env-generate
fi

# On KDE, enable menu sync and SDDM (but NOT here — SDDM/dbus are enabled
# by the installer post-install, not on the live ISO, so the PyQt6 installer
# can launch via startx instead of a display manager).
if [ "$PROFILE" = "kde" ] && [ -f /etc/systemd/system/muluos-menu-sync.service ]; then
    systemctl enable muluos-menu-sync
fi

# Profile marker so the installer knows which services to enable on the target.
echo "$PROFILE" > /etc/muluos-profile

# ── Executable bits on overlay scripts ───────────────────────────────────
for f in /usr/libexec/muluos/launch-bundle /usr/libexec/muluos/bundle-thumbnailer; do
    [ -f "$f" ] && chmod 0755 "$f"
done

# ── Refresh MIME and desktop databases ───────────────────────────────────
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

# ── Wheel/sudo group passwordless sudo on live media ─────────────────────
echo "%sudo ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/muluos-live-nopasswd
chmod 0440 /etc/sudoers.d/muluos-live-nopasswd

# ── Live-mode TTY auto-login (systemd drop-in) ──────────────────────────
# On the live ISO, root is auto-logged in on tty1. If muluos.mode=live is
# present on the kernel command line, the auto-login fires; otherwise the
# standard getty runs.  This is a drop-in override — the base getty@.service
# from systemd is untouched.
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/muluos-autologin.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
UNIT

# Conditionally restrict the auto-login override to live-mode only by
# wrapping it in an ExecCondition that checks /proc/cmdline.
cat > /usr/local/sbin/muluos-live-check <<'CHECK'
#!/bin/sh
grep -q "muluos.mode=live" /proc/cmdline 2>/dev/null
CHECK
chmod 0755 /usr/local/sbin/muluos-live-check

# ── Live-mode X auto-start for root on tty1 ─────────────────────────────
cat > /root/.bash_profile <<'BASH'
if [ "$(tty)" = "/dev/tty1" ] \
   && grep -q "muluos.mode=live" /proc/cmdline 2>/dev/null \
   && [ -z "${MULUOS_X_STARTED:-}" ]; then
    export MULUOS_X_STARTED=1
    exec startx
fi
BASH

cat > /root/.xinitrc <<'XINIT'
#!/bin/sh
xset s off -dpms 2>/dev/null || true
cd /opt
exec python3 -m installer.main
XINIT
chmod +x /root/.xinitrc

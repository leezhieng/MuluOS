#!/bin/sh
# Runs inside the freshly-bootstrapped rootfs. $1 is the profile name.
set -eu
PROFILE="${1:-cli}"

rc-update add devfs sysinit
rc-update add dmesg sysinit
rc-update add mdev sysinit
rc-update add hwclock boot
rc-update add modules boot
rc-update add sysctl boot
rc-update add hostname boot
rc-update add bootmisc boot
rc-update add syslog boot
rc-update add networkmanager default
rc-update add sshd default

# Make /usr/lib/muluos importable as a Python site dir so apps can
# `import muluos_registry` regardless of which python3.X is installed.
if command -v python3 >/dev/null 2>&1; then
    SITE=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>/dev/null || true)
    if [ -n "$SITE" ]; then
        mkdir -p "$SITE"
        echo "/usr/lib/muluos" > "$SITE/muluos.pth"
    fi
fi

# Enable the registry daemon in default runlevel (needed by every profile).
[ -f /etc/init.d/muluos-registryd ] && rc-update add muluos-registryd default

# Regenerate the environment profile (/etc/profile.d/muluos-env.sh) from the
# registry on every boot. Applies to all profiles.
[ -f /etc/init.d/muluos-env-generate ] && rc-update add muluos-env-generate default

# Profile marker so the installer knows which services to enable on the target.
# SDDM/dbus are NOT enabled here; the live ISO must boot to console+startx so
# the PyQt6 installer can launch. Installer post-install enables them on KDE.
echo "$PROFILE" > /etc/muluos-profile

# Re-belt-and-suspenders the bundle launcher / thumbnailer executable bits
# in case the host copy lost the mode bits.
for f in /usr/libexec/muluos/launch-bundle /usr/libexec/muluos/bundle-thumbnailer; do
    [ -f "$f" ] && chmod 0755 "$f"
done

# Refresh MIME and desktop databases so the .exe bundle association is live.
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

# Wheel group sudo without password during install media; tighten on real install.
echo "%wheel ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel-nopasswd
chmod 0440 /etc/sudoers.d/wheel-nopasswd

# Live-mode detection at runtime via /proc/cmdline (muluos.mode=live, set in
# the live ISO's GRUB entries). Same files exist on installed systems but the
# checks are no-ops there, so no install-time teardown is needed.
mkdir -p /usr/local/sbin
cat > /usr/local/sbin/muluos-tty1 <<'EOF'
#!/bin/sh
if grep -q "muluos.mode=live" /proc/cmdline 2>/dev/null; then
    exec agetty --autologin root --noclear 38400 tty1
fi
exec /sbin/getty 38400 tty1
EOF
chmod 0755 /usr/local/sbin/muluos-tty1
sed -i -E "s|^tty1::respawn:.*|tty1::respawn:/usr/local/sbin/muluos-tty1|" /etc/inittab

cat > /root/.profile <<'EOF'
if [ "$(tty)" = "/dev/tty1" ] \
   && grep -q "muluos.mode=live" /proc/cmdline 2>/dev/null \
   && [ -z "${MULUOS_X_STARTED:-}" ]; then
    export MULUOS_X_STARTED=1
    exec startx
fi
EOF

cat > /root/.xinitrc <<'EOF'
#!/bin/sh
xset s off -dpms 2>/dev/null || true
cd /opt
exec python3 -m installer.main
EOF
chmod +x /root/.xinitrc

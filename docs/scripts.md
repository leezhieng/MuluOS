# `scripts/` — host and chroot helpers

This directory holds shell scripts that the build system invokes at
specific moments. Anything that needs to run inside the target rootfs
lives here; per-application overlays live under `assets/` instead.

## `chroot-hook.sh`

The single script the builder copies into the freshly-bootstrapped
rootfs and executes via `chroot`. It is *the* place to do anything that
needs to run "inside the target system before the image is sealed":
enabling services, refreshing caches, generating files whose paths
depend on installed package versions.

**Invocation.** Called by `muluos.builder.rootfs._run_chroot_hook()`
with one argument — the profile name (`cli` or `kde`):

```
chroot <rootfs> /tmp/chroot-hook.sh <profile>
```

The script is deleted after it runs.

**What it does, in order:**

1. **OpenRC sysinit/boot services** — `devfs`, `dmesg`, `mdev`,
   `hwclock`, `modules`, `sysctl`, `hostname`, `bootmisc`, `syslog`.
   These are required for any Alpine-derived system to come up.
2. **Default-runlevel services** — `networkmanager`, `sshd`. These run
   regardless of profile.
3. **Python site-dir bootstrap** — queries the installed `python3` for
   its `purelib` directory and drops a `muluos.pth` file there pointing
   at `/usr/lib/muluos`. This makes `import muluos_registry` work in
   any process without hardcoding a python3.X minor version.
4. **Registry daemon enable** — adds `muluos-registryd` to the default
   runlevel. This is core to every profile; the daemon binds the socket
   that the bundle launcher needs.
5. **KDE-only services** — if `$PROFILE = kde`, enables `sddm` and
   `dbus`.
6. **Sudo for wheel** — drops a wheel-NOPASSWD entry in
   `/etc/sudoers.d/`. Intended for the live-install media; the
   installer should tighten this on the real installed system.
7. **Live-mode installer auto-launch** — writes a `profile.d` snippet
   that runs `python3 -m installer.main` on the first root login if no
   one has run it yet. Lets the install ISO boot straight into the
   installer.
8. **Bundle launcher / thumbnailer chmod** — defensive chmod 0755 on
   the `.exe` bundle support scripts in case `shutil.copytree` lost the
   mode bits.
9. **MIME and desktop database refresh** — runs `update-mime-database`
   and `update-desktop-database` (guarded by `command -v`) so the
   `application/x-muluos-bundle` MIME type, the bundle launcher
   `.desktop`, and the Dolphin service menu are all picked up by KDE.

If you need to add a step, put it in the right band: runlevel changes
go alongside the existing `rc-update add` lines, file generation goes
near the existing `cat > ... <<'EOF'` blocks, and anything that
manipulates caches goes near the bottom with the database refreshes.

**What does NOT belong here:**

- Per-application config that ships verbatim — that's an overlay
  (`assets/<name>/`) plus a `muluos.builder.<name>.install()` helper.
- Anything you'd want to re-run on a *running* system — those go in
  CLI tools (`muluos-bundle install`, etc.).
- Anything specific to the build host. Host-side prep lives in
  `muluos/builder/host.py`.

## Adding new scripts

If a step is genuinely shell-shaped and runs in the chroot, append to
`chroot-hook.sh` rather than adding a second script — keeping a single
entry point makes the chroot phase easy to reason about.

If the step needs to be re-runnable on the installed system (e.g.,
periodic maintenance), make it a CLI tool in an overlay (mirroring
`/usr/bin/muluos-reg` and `/usr/bin/muluos-bundle`) and just *enable*
it from `chroot-hook.sh`.

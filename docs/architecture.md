# MuluOS architecture

A guide to what lives in this repo, what each module does, and how the
build flows together.

## Layout

```
MuluOS/
├── build.py                 # entry point: orchestrates a build
├── muluos/                  # the build-system Python package (runs on host)
│   ├── config.py            # constants: paths, Alpine branch, mirror, image
│   ├── builder/             # rootfs/iso/kernel/docker glue
│   ├── installer/           # OS installer (lands in the image at /opt/installer)
│   └── profiles/            # package set per profile (cli, kde, base)
├── assets/
│   ├── branding/            # logos, plymouth, sddm theme
│   ├── bundle/              # overlay: MIME, launcher, thumbnailer (.exe bundle support)
│   └── registry/            # overlay: registry daemon, client lib, CLIs
├── scripts/
│   └── chroot-hook.sh       # runs inside the freshly-bootstrapped rootfs
├── kio-worker/              # C++/Qt scaffolds (not part of the Python build)
└── docs/
```

## Two halves: build-time vs runtime

**Build-time Python lives in `muluos/`.** It runs on the host that's
producing the ISO. It is *never installed into the target system*.
Internally it has:

- `muluos.config` — constants used everywhere (mirror URLs, paths).
- `muluos.profiles.{base, cli, kde}` — flat `PACKAGES` lists. `base` is
  shared by every profile; `cli` and `kde` add on top.
- `muluos.builder.rootfs.build()` — the master function. It runs `apk`
  to bootstrap an Alpine rootfs, copies the installer into `/opt/installer`,
  installs the registry overlay, installs the bundle overlay, then runs
  the chroot hook to enable services and refresh databases.
- `muluos.builder.{registry, bundle}` — host-side helpers that
  recursively copy an overlay tree from `assets/` into the rootfs and
  chmod the scripts inside it. Same shape, different overlays.
- `muluos.builder.iso` / `kernel` / `docker` / `host` / `native` —
  surface for the different build paths (running on the host directly,
  inside Docker, etc.).
- `muluos.installer` — the GUI/CLI installer that ships *inside* the
  image. Copied verbatim to `/opt/installer/` and started by the
  per-profile auto-login (see [scripts.md](scripts.md)).

**Runtime overlays live in `assets/{registry,bundle}/`.** Each overlay
is a tree mirroring `/` so the builder can `shutil.copytree(..., dirs_exist_ok=True)`
it into the rootfs verbatim. Anything that lands on the running system
goes through an overlay.

| Overlay | Lands at | Contents |
|---|---|---|
| `assets/bundle/` | rootfs `/` | MIME XML, thumbnailer, .desktop handler, KIO service menu, the `launch-bundle` script |
| `assets/registry/` | rootfs `/` | The registry daemon, OpenRC service, client library at `/usr/lib/muluos/`, `muluos-reg` and `muluos-bundle` CLIs |

## Build flow

1. `build.py` picks a profile (cli/kde) and arch.
2. `muluos.builder.rootfs.build()`:
   1. Calls `apk` with the union of `profiles.base.PACKAGES` and the
      profile's `PACKAGES`. The rootfs ends up under `build/.../rootfs/`.
   2. Writes `/etc/apk/repositories`.
   3. Copies `muluos/installer/` to `<rootfs>/opt/installer`.
   4. Calls `registry.install(rootfs)` — copies `assets/registry/`.
   5. Calls `bundle.install(rootfs)` — copies `assets/bundle/`.
   6. Drops [scripts/chroot-hook.sh](../scripts/chroot-hook.sh) into the
      rootfs and chroots in to run it.
3. The chroot hook enables OpenRC services (`networkmanager`,
   `sshd`, `muluos-registryd`, and on KDE `sddm`/`dbus`), drops a
   `muluos.pth` into Python's site-packages so `import muluos_registry`
   works, sets up the live-mode installer auto-launch, and refreshes
   the MIME / desktop databases on KDE profiles.
4. The ISO build wraps the prepared rootfs (see `builder/iso.py`).

## Runtime systems

Once installed, the running system has:

```
┌────────────────────────────┐
│ Plasma session             │
│  ┌──────────────────────┐  │
│  │ Dolphin              │──┼── MIME: application/x-muluos-bundle
│  │                      │  │     → /usr/share/applications/muluos-bundle.desktop
│  │                      │  │     → /usr/libexec/muluos/launch-bundle <bundle>
│  └──────────────────────┘  │
│                            │
│  Thumbnailer (on demand)   │
│   /usr/share/thumbnailers/ │
│   muluos-bundle.thumbnailer│
│                            │
└────────────────────────────┘
            │
            │ exec
            ▼
┌────────────────────────────┐         ┌──────────────────────────────┐
│ launch-bundle (script)     │ socket  │ muluos-registryd             │
│                            │────────▶│ (root, OpenRC)               │
│  - reads Info.json         │  bind   │  - SQLite at /var/lib/muluos │
│  - dup2(sock, fd 3)        │         │  - bundles + entries tables  │
│  - exec child binary       │         │  - per-conn Session state    │
└────────────────────────────┘         └──────────────────────────────┘
            │                                      ▲
            │ exec, fd 3 inherited                 │ frame over fd
            ▼                                      │
┌────────────────────────────┐                     │
│ Bundle binary (the app)    │─────────────────────┘
│  - import muluos_registry  │
│  - reads MULUOS_REGISTRY_FD│
│  - reg.get(), reg.set()    │
└────────────────────────────┘
```

The installer (or `muluos-bundle install`) talks to the same daemon
directly via the socket and writes machine-scope entries / the
`bundles` table. See [registry.md](registry.md) for the wire protocol
and security model, [bundles.md](bundles.md) for the bundle format.

## Adding a new overlay

If you want to ship more files into the rootfs (a new daemon, a config
template, etc.), the pattern is:

1. Create `assets/<name>/` and mirror the rootfs structure inside it.
2. Add `muluos/builder/<name>.py` that has an `install(rootfs_dir)`
   function — see `registry.py` / `bundle.py` for the shape.
3. Call it from `muluos/builder/rootfs.py` after the existing overlays.
4. If the overlay introduces a service or needs database refreshes,
   add the line to [scripts/chroot-hook.sh](../scripts/chroot-hook.sh).

Keep the overlay's contents **idempotent**: `shutil.copytree(...,
dirs_exist_ok=True)` will overwrite, but the chroot hook can run more
than once during iteration.

## Not-yet-implemented pieces

- **`kio-worker/`** is a C++/Qt scaffold for making `.exe` bundles
  appear truly opaque in Dolphin. It is not part of the Python build
  and is not auto-built into the image yet. See its
  [README](../kio-worker/muluos-bundle/README.md).
- **`muluos.installer`** is currently scaffolding; package management
  on the running system (the thing that would call `muluos-bundle install`)
  is not wired up yet.
